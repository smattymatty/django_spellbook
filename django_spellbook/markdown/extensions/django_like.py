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
DJANGO_INLINE_TAGS = {
    'static', 'url', 'include', 'load', 'csrf_token'
}
DJANGO_INLINE_TAG_REGEX = r'({%\s*(\b(?:' + '|'.join(DJANGO_INLINE_TAGS) + r')\b)\s*.*?\s*%})'

class DjangoLikeTagInlineProcessor(InlineProcessor):
    """ Handles inline Django tags like {% static 'path' %} or {% url 'name' %}. """
    def __init__(self, pattern: str, md: Optional[Any] = None):
        super().__init__(pattern)
        self.markdown = md

    def handleMatch(self, m: re.Match, data: str) -> Tuple[Optional[ElementTree.Element], Optional[int], Optional[int]]:
        """ Process a match found by the regex. """
        full_tag_text = m.group(1)
        el = ElementTree.Element('django-tag')
        el.text = full_tag_text
        return el, m.start(0), m.end(0)

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
        'extends', 'load', 'with', 'csrf_token', 'show_metadata'
    }

    DJANGO_BLOCK_TAGS = {
        'if': 'endif',
        'for': 'endfor',
        'block': 'endblock',
        'with': 'endwith',
    }
    
    DJANGO_INLINE_TAGS = DJANGO_INLINE_TAGS

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
        if tag in DJANGO_INLINE_TAGS:
            return False # Signal block NOT handled by this processor

        # --- If we are here, it's a block/custom tag, so proceed ---
        blocks.pop(0) # Pop the block *only* if we are handling it
        attrs_string = match.group(2).strip()
        before_content = original_block[:match.start()]
        remaining_content_in_block = original_block[match.end():]

        # Process 'before' content *only* if we are handling the block/custom tag
        if before_content:
            self.parser.parseBlocks(parent, [before_content])

        # --- Dispatch (only block/custom tags reach here) ---
        if tag in self.DJANGO_BUILT_INS: # Must be block built-in (if, for, else...)
            return self._handle_django_tag(parent, blocks, remaining_content_in_block, match)
        else: # Custom elements
            return self._handle_custom_element(parent, blocks, remaining_content_in_block, tag, attrs_string)

    # -- Handlers for Different Tag Types --
    def _handle_django_tag(
        self, parent: ElementTree.Element,
        blocks: List[str], first_content_chunk: str,
        match: re.Match
        ) -> bool:
        """ Handle built-in Django template tags (block tags, else/elif). """
        tag: str = match.group(1)
        full_opening_tag: str = match.group(0)

        # Handle block-level Django tags ({% if %}, {% for %}, etc.)
        if tag in self.DJANGO_BLOCK_TAGS:
            # This helper might need similar preprocessing if it uses parseBlocks internally
            return handle_django_block_tag(self, parent, blocks, first_content_chunk, tag, full_opening_tag)

        # Handle OTHER built-in tags (else, elif - treated as block boundaries)
        tag_element: ElementTree.Element = ElementTree.SubElement(parent, 'django-tag')
        tag_element.text = full_opening_tag

        if first_content_chunk:
            blocks.insert(0, first_content_chunk)

        return True
    
    def _handle_custom_element(
        self, parent: ElementTree.Element,
        blocks: List[str], first_content_chunk: str,
        tag: str, attrs_string: str
        ) -> bool:
        """ Handle custom HTML-like elements {% tag ... %}content{% endtag %}. """
        element = ElementTree.SubElement(parent, tag)
        self._parse_attributes(element, attrs_string)

        content_result: NestedContentResult = process_nested_content(
            self, tag, first_content_chunk, blocks
        )

        if content_result.inner_content:
            inner_content = content_result.inner_content
            
            # Split content into proper blocks while preserving list structure
            # The key insight: markdown needs blank lines to separate blocks properly
            lines = inner_content.split('\n')
            blocks_to_parse = []
            current_block_lines = []
            in_list = False
            
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # Check if this line starts a list
                is_list_item = stripped.startswith(('- ', '* ', '+ ')) or (
                    stripped and stripped[0].isdigit() and '. ' in stripped[:4]
                )
                
                # If we hit an empty line, end current block
                if not stripped:
                    if current_block_lines:
                        blocks_to_parse.append('\n'.join(current_block_lines))
                        current_block_lines = []
                        in_list = False
                    i += 1
                    continue
                
                # If we transition from non-list to list, end current block
                if is_list_item and not in_list and current_block_lines:
                    blocks_to_parse.append('\n'.join(current_block_lines))
                    current_block_lines = []
                
                # If we transition from list to non-list, end current block  
                if not is_list_item and in_list and current_block_lines:
                    blocks_to_parse.append('\n'.join(current_block_lines))
                    current_block_lines = []
                
                current_block_lines.append(line)
                in_list = is_list_item
                i += 1
            
            # Add final block
            if current_block_lines:
                blocks_to_parse.append('\n'.join(current_block_lines))
            
            # Process Django tags to ensure proper spacing  
            final_blocks = []
            for block in blocks_to_parse:
                if not block.strip():
                    continue
                    
                # Handle Django tags in blocks
                if self.RE_START.search(block):
                    modified_content = ""
                    last_pos = 0
                    
                    for match in self.RE_START.finditer(block):
                        tag_name = match.group(1)
                        is_block_tag = (
                            tag_name not in self.DJANGO_INLINE_TAGS and
                            not tag_name.startswith('end')
                        )
                        
                        if is_block_tag:
                            # Add content before tag
                            preceding = block[last_pos:match.start()].strip()
                            if preceding:
                                final_blocks.append(preceding)
                            # Add tag as separate block
                            final_blocks.append(match.group(0))
                            last_pos = match.end()
                    
                    # Add remaining content
                    remaining = block[last_pos:].strip()
                    if remaining:
                        final_blocks.append(remaining)
                else:
                    final_blocks.append(block)
            
            # Use temporary parent for safety
            temp_parent = ElementTree.Element('div')
            self.parser.parseBlocks(temp_parent, final_blocks)

            # Transfer children
            for child in list(temp_parent):
                element.append(child)

        blocks[:] = content_result.remaining_blocks
        return True

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