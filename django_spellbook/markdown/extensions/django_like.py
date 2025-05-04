# django_spellbook/markdown/extensions/django_like.py
import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree
from typing import List, Optional, Tuple

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
        'static', 'url', 'include', 'if', 'for', 'block',
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
        """
        Process the block and handle Django-like tags.
        This is a required method for the extension to be registered.
        
        This method is called by the Markdown parser when it encounters a block
        that contains a Django-like tag. It handles the tag and any content
        before or after it.
        
        Args:
            parent: Parent XML element. This is the root element of the rendered HTML.
            blocks: List of text blocks to process. This is the list of markdown blocks
                    that have been split into individual lines by the parser.
                    
                    The first block is the original block that contained the Django-like tag.
                    Subsequent blocks are the content that came before and after the tag.
                    
                    Example: ['{% div %}', 'This is the content before the tag.', '{% enddiv %}']
                    
        Returns:
            True if processing was successful, False otherwise. If False, the original
            block is added back to the list and processing stops.
        """
        extraction_result: Optional[
            Tuple[str, str, str, str, re.Match]
            ] = self._find_and_extract_opening_tag(blocks)

        if extraction_result is None:
            # No valid tag found, or block list was empty.
            # We didn't pop anything if no tag was found.
            return False

        tag, attrs_string, before_content, remaining_content_in_block, match = extraction_result

        # Process 'before' content if it exists
        if before_content:
            self.parser.parseBlocks(parent, [before_content])

        # --- Dispatch based on tag type ---
        if tag in self.DJANGO_BUILT_INS:
            return self._handle_django_tag(parent, blocks, remaining_content_in_block, match)
        else:
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
        full_opening_tag: str = match.group(0) # The complete {% ... %} tag text

        # Handle block-level Django tags ({% if %}, {% for %}, etc.)
        if tag in self.DJANGO_BLOCK_TAGS:
            # Pass the blocks list as received
            return handle_django_block_tag(self, parent, blocks, first_content_chunk, tag, full_opening_tag)

        # Handle single Django tags ({% url %}, {% static %}, etc.)
        tag_element: ElementTree.Element = ElementTree.SubElement(parent, 'django-tag')
        tag_element.text = full_opening_tag

        # Put the remaining content from the original block back at the
        # beginning of the blocks list for standard parsing.
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
            DjangoLikeTagProcessor(md.parser), 'django_like_tag', 175
        )

def makeExtension(**kwargs) -> DjangoLikeTagExtension:
    """ Boilerplate factory function. """
    return DjangoLikeTagExtension(**kwargs)