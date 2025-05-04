# django_spellbook/markdown/extensions/django_like.py
import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from xml.etree import ElementTree
from typing import List, Optional, Tuple, Any

from django_spellbook.markdown.extensions.tag_stats import (
    NestedContentResult
)

from django_spellbook.markdown.attribute_parser import parse_attributes

from django_spellbook.markdown.extensions.django_builtin_tag_helpers import (
    handle_django_block_tag
)
from django_spellbook.markdown.extensions.custom_tag_parser import (
    process_nested_content
)

# --- Define the set of tags handled by the Inline Processor ---
# These are tags that should render inline within text, not break blocks.
# Excludes block tags (if, for, etc.) and potentially problematic ones like else/elif/extends
DJANGO_INLINE_TAGS = {
    'static', 'url', 'include', 'load', 'csrf_token'
}

# --- Regex for the Inline Processor ---
# Captures the entire tag {% ... %} for replacement.
# Group 1: The full tag {% ... %}
# Group 2: The tag name (e.g., 'static', 'url')
DJANGO_INLINE_TAG_REGEX = r'({%\s*(\b(?:' + '|'.join(DJANGO_INLINE_TAGS) + r')\b)\s*.*?\s*%})'


# --- Inline Processor Class ---
class DjangoLikeTagInlineProcessor(InlineProcessor):
    """
    Handles inline Django tags like {% static 'path' %} or {% url 'name' %}.

    This processor identifies specific inline Django tags within text nodes
    and wraps them in a <django-tag> element without breaking paragraph blocks.
    """
    def __init__(self, pattern: str, md: Optional[Any] = None):
        """
        Initialize the inline processor.

        Args:
            pattern: The regex pattern to match inline tags.
            md: The Markdown instance (optional but recommended by Pattern).
        """
        super().__init__(pattern)
        self.markdown = md # Storing md instance is good practice if needed later

    def handleMatch(self, m: re.Match, data: str) -> Tuple[Optional[ElementTree.Element], Optional[int], Optional[int]]:
        """
        Process a match found by the regex.

        Args:
            m: The regex match object.
            data: The entire block of text being processed.

        Returns:
            A tuple (element, start_index, end_index) or (None, None, None).
        """
        # Group 1 contains the entire matched tag {% ... %}
        full_tag_text = m.group(1)

        # Create the <django-tag> element
        el = ElementTree.Element('django-tag')
        # Set its text content to the original tag string
        el.text = full_tag_text

        # Return the element and the start/end indices of the match
        # m.start(0) / m.end(0) refer to the indices of the entire match (group 0)
        return el, m.start(0), m.end(0) # <--- Return the tuple

class DjangoLikeTagProcessor(BlockProcessor):
    """
    A Markdown block processor that handles Django-like template tags.

    This processor allows using Django-style template tags within markdown content,
    supporting both custom HTML elements with attributes and built-in Django template tags.
    It uses an external parser to handle attribute string parsing, including shortcuts.

    Supported syntax:
    - Custom elements: {% tag class="value" id="myid" %}content{% endtag %}
    - Class shortcuts: {% tag .classname %}content{% endtag %}
    - ID shortcuts: {% tag #myid %}content{% endtag %}
    - Built-in Django tags: {% url 'name' %}, {% static 'path' %}, {% include 'template' %}

    Attributes:
        DJANGO_BUILT_INS (set): Set of built-in Django template tags to preserve.
        DJANGO_BLOCK_TAGS (dict): Mapping of Django block tags to their closing tags.
        RE_START (Pattern): Regex for matching opening tags {% tag ... %}.
        RE_END (Pattern): Regex for matching closing tags {% endtag %}.
    """

    DJANGO_BUILT_INS = {
        'static', 'url', 'include', 'if', 'for', 'block', 'else', 'elif',
        'extends', 'load', 'with', 'csrf_token'
    }

    DJANGO_BLOCK_TAGS = {
        'if': 'endif',
        'for': 'endfor',
        'block': 'endblock',
        'with': 'endwith',
    }

    # Regex for start and end tags remain
    RE_START = re.compile(r'{%\s*(?!end)(\w+)([\s\S]*?)%}') # Capture tag name and everything else
    # unless it's an 'end' tag
    RE_END = re.compile(r'{%\s*end(\w+)\s*%}') # Capture closing tag name

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        """
        Test if the block contains a valid opening Django-like tag.
        This is a required method for the extension to be registered.

        Args:
            parent: Parent XML element.
            block: Text block to test.

        Returns:
            True if block contains a potential Django-like opening tag
            that doesn't start with 'end'.
        """
        match = self.RE_START.search(block)
        # Ensure a match exists AND the tag name doesn't start with 'end'
        return bool(match and not match.group(1).startswith('end'))

    def run(self, parent: ElementTree.Element, blocks: List[str]) -> bool:
        """ Process the block and handle Django-like tags. """
        # --- Test the tag type BEFORE popping or processing ---
        original_block = blocks[0]
        match = self.RE_START.search(original_block)

        if not match or match.group(1).startswith('end'):
            return False # Not a tag we handle / end tag

        tag = match.group(1)

        # --- If it's an INLINE tag, bail out IMMEDIATELY ---
        # Let standard paragraph processing + InlineProcessor handle it.
        if tag in DJANGO_INLINE_TAGS:
            return False # Signal block NOT handled by this processor

        # --- If we are here, it's a block/custom tag, so proceed ---
        # --- Now we can pop the block and extract parts ---
        blocks.pop(0) # Pop the block *only* if we are handling it
        attrs_string = match.group(2).strip()
        before_content = original_block[:match.start()]
        remaining_content_in_block = original_block[match.end():]

        # Process 'before' content *only* if we are handling the block/custom tag
        if before_content:
            self.parser.parseBlocks(parent, [before_content])

        # --- Dispatch (only block/custom tags reach here) ---
        if tag in self.DJANGO_BUILT_INS: # Must be block built-in (if, for, else...)
            # Pass the original match object
            return self._handle_django_tag(parent, blocks, remaining_content_in_block, match)
        else: # Custom elements
             # Pass the original match object (or just the tag/attrs like before)
            return self._handle_custom_element(parent, blocks, remaining_content_in_block, tag, attrs_string)


    # -- Initial Tag Extraction Helper --
    def _find_and_extract_opening_tag(self, blocks: List[str]) -> Optional[Tuple[str, str, str, str, re.Match]]:
        """
        Finds the first opening tag, extracts info, and handles 'before' content.
        For use by run()
        Pops the first block from the list if a valid tag is found.
        
        Args:
            blocks: List of text blocks to process. This is the list of markdown blocks
                    that have been split into individual lines by the parser.
                    
                    The first block is the original block that contained the Django-like tag.
                    Subsequent blocks are the content that came before and after the tag.
                    
                    Example: ['{% div %}', 'This is the content before the tag.', '{% enddiv %}']
                    
        Returns:
            A tuple containing:
            - The tag name (e.g., 'div', 'span')
            - The raw string containing tag attributes (e.g., 'class="my-class"')
            - The content before the tag (e.g., 'This is the content before the tag.')
            - The content after the tag (e.g., 'This is the content after the tag.')
            - The regex match object for the opening tag (e.g., re.Match object)
            
            - None if no valid tag is found
        """
        if not blocks:
            return None # pragma: no cover

        original_block = blocks[0] # Peek, don't pop yet
        match = self.RE_START.search(original_block)

        if not match or match.group(1).startswith('end'):
            return None # No valid opening tag found

        # Now we know we'll process it, so pop it
        blocks.pop(0)

        tag = match.group(1)
        attrs_string = match.group(2).strip()
        before_content = original_block[:match.start()]
        remaining_content_in_block = original_block[match.end():]

        return tag, attrs_string, before_content, remaining_content_in_block, match

    # -- Handlers for Different Tag Types --
    def _handle_django_tag(
        self, parent: ElementTree.Element,
        blocks: List[str], first_content_chunk: str,
        match: re.Match
        ) -> bool:
        """
        Handle built-in Django template tags (single or block).
        For use by run() if the tag is in self.DJANGO_BUILT_INS.
        {% if condition %} or {% for item in items %} is handled by this method.

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: The portion of the original block after the opening tag.
            match: Regex match object for the opening tag.

        Returns:
            True if processing was successful.
        """
        tag: str = match.group(1)
        full_opening_tag: str = match.group(0)

        # Handle block-level Django tags ({% if %}, {% for %}, etc.)
        if tag in self.DJANGO_BLOCK_TAGS:
            return handle_django_block_tag(self, parent, blocks, first_content_chunk, tag, full_opening_tag)

        # Handle OTHER built-in tags found by the block processor.
        # This includes else/elif, and potentially inline tags if they somehow
        # started a block or weren't processed inline first.
        # Safest approach is to wrap them in <django-tag> here too.
        # This provides a fallback.
        tag_element: ElementTree.Element = ElementTree.SubElement(parent, 'django-tag')
        tag_element.text = full_opening_tag

        # Put the remaining content back for standard parsing.
        if first_content_chunk:
            blocks.insert(0, first_content_chunk)

        return True
    
    def _handle_custom_element(
        self, parent: ElementTree.Element,
        blocks: List[str], first_content_chunk: str,
        tag: str, attrs_string: str
        ) -> bool:
        """
        Handle custom HTML-like elements {% tag ... %}content{% endtag %}.

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: The portion of the original block after the opening tag.
            tag: The tag name (e.g., 'div').
            attrs_string: The raw attribute string from the opening tag.

        Returns:
            True if processing was successful.
        """
        # Create the element *first*
        element = ElementTree.SubElement(parent, tag) # Use tag name as element name
        # Parse and set attributes
        self._parse_attributes(element, attrs_string)

        # --- Process nested content using the NEW refactored method ---
        # This call now uses the state class and helpers internally
        content_result: NestedContentResult = process_nested_content(
            self, tag, first_content_chunk, blocks
        )

        # Parse the extracted inner content recursively
        if content_result.inner_content:
            # Use the robust parsing method with a temporary parent
            temp_parent = ElementTree.Element('div')
            self.parser.parseBlocks(temp_parent, content_result.inner_content.split('\n\n'))
            # Transfer children and text/tail from temp_parent
            if temp_parent.text and temp_parent.text.strip():
                element.text = (element.text or "") + temp_parent.text # pragma: no cover
            for child in list(temp_parent):
                element.append(child) # Moves child including its text and tail

        # Update the main blocks list with remaining blocks
        blocks[:] = content_result.remaining_blocks

        return True # Assume processed

    # --- Attribute Parsing Helper ---
    def _parse_attributes(self, element: ElementTree.Element, attrs_string: str) -> None:
        """ Parses attribute string and sets them on the element. """
        # (Keep this helper method)
        attributes = parse_attributes(attrs_string)
        for key, value in attributes.items():
            element.set(key, value)


# --- Extension Boilerplate ---
class DjangoLikeTagExtension(Extension):
    """ Markdown extension for handling Django-like template tags. """
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(
            DjangoLikeTagProcessor(md.parser), 
            'django_like_tag', 
            175
        )
        md.inlinePatterns.register(
            DjangoLikeTagInlineProcessor(DJANGO_INLINE_TAG_REGEX, md), 
            'django_inline', 
            170
        )

def makeExtension(**kwargs) -> DjangoLikeTagExtension:
    """ Boilerplate factory function. """
    return DjangoLikeTagExtension(**kwargs)