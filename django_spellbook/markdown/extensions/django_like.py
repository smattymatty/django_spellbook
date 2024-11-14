import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree
from typing import List, Optional, Dict, Any
from django.template import Template, Context
from django.template.loader import render_to_string


class DjangoLikeTagProcessor(BlockProcessor):
    """
    A Markdown block processor that handles Django-like template tags.

    This processor allows using Django-style template tags within markdown content,
    supporting both custom HTML elements with attributes and built-in Django template tags.

    Supported syntax:
    - Custom elements: {% tag class="value" id="myid" %}content{% endtag %}
    - Class shortcuts: {% tag .classname %}content{% endtag %}
    - ID shortcuts: {% tag #myid %}content{% endtag %}
    - Built-in Django tags: {% url 'name' %}, {% static 'path' %}, {% include 'template' %}

    Attributes:
        DJANGO_BUILT_INS (set): Set of built-in Django template tags to preserve
        RE_START (Pattern): Regex for matching opening tags
        RE_END (Pattern): Regex for matching closing tags
        RE_CLASS (Pattern): Regex for matching class attributes
        RE_ID (Pattern): Regex for matching ID attributes
        RE_ATTR (Pattern): Regex for matching general attributes
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

    RE_START = re.compile(r'{%\s*(\w+)([\s\S]+?)%}')
    RE_END = re.compile(r'{%\s*end(\w+)\s*%}')
    RE_CLASS = re.compile(r'\.([:\w-]+)')
    RE_ID = re.compile(r'#([\w-]+)')
    RE_ATTR = re.compile(r'([@:\w-]+)=[\'"]([^\'"]+)[\'"]')

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        """
        Test if the block should be processed.

        Args:
            parent: Parent XML element
            block: Text block to test

        Returns:
            bool: True if block contains a Django-like tag
        """
        return bool(self.RE_START.search(block))

    def run(self, parent: ElementTree.Element, blocks: List[str]) -> bool:
        """
        Process the block and handle Django-like tags.

        Args:
            parent: Parent XML element
            blocks: List of text blocks to process

        Returns:
            bool: True if processing was successful

        Raises:
            ValueError: If opening and closing tags don't match
        """
        block = blocks.pop(0)
        m = self.RE_START.search(block)

        if not m:
            return False

        tag = m.group(1)
        attrs_string = m.group(2)

        # Handle built-in Django tags
        if tag in self.DJANGO_BUILT_INS:
            return self._handle_django_tag(parent, blocks, block, m)

        # Handle custom HTML elements
        return self._handle_custom_element(parent, blocks, block, m, tag, attrs_string)

    def _handle_django_tag(self, parent: ElementTree.Element,
                           blocks: List[str], block: str,
                           match: re.Match) -> bool:
        """
        Handle built-in Django template tags.

        Args:
            parent: Parent XML element
            blocks: List of text blocks
            block: Current block being processed
            match: Regex match object

        Returns:
            bool: True if processing was successful
        """
        tag = match.group(1)
        before = block[:match.start()]
        if before:
            self.parser.parseBlocks(parent, [before])

        # Handle block-level Django tags
        if tag in self.DJANGO_BLOCK_TAGS:
            return self._handle_django_block_tag(parent, blocks, block, match)

        # Handle single Django tags
        tag_text = ElementTree.SubElement(parent, 'django-tag')
        tag_text.text = block[match.start():match.end()]

        after = block[match.end():]
        if after:
            self.parser.parseBlocks(parent, [after])

        return True

    def _handle_django_block_tag(self, parent: ElementTree.Element,
                                 blocks: List[str], block: str,
                                 match: re.Match) -> bool:
        """
        Handle Django block-level tags like if, for, etc.

        Args:
            parent: Parent XML element
            blocks: List of text blocks
            block: Current block being processed
            match: Regex match object

        Returns:
            bool: True if processing was successful
        """
        tag = match.group(1)
        end_tag = self.DJANGO_BLOCK_TAGS.get(tag)

        # Create opening tag
        opening_tag = ElementTree.SubElement(parent, 'django-tag')
        opening_tag.text = block[match.start():match.end()]

        # Get content until closing tag
        content = block[match.end():]
        while blocks and f'{{% {end_tag} %}}' not in content:
            content += '\n' + blocks.pop(0)

        # Split at closing tag
        if f'{{% {end_tag} %}}' in content:
            parts = content.split(f'{{% {end_tag} %}}', 1)
            inner_content, after = parts
        else:
            inner_content = content
            after = ''

        # Process inner content
        if inner_content.strip():
            self.parser.parseChunk(parent, inner_content)

        # Add closing tag
        closing_tag = ElementTree.SubElement(parent, 'django-tag')
        closing_tag.text = f'{{% {end_tag} %}}'

        # Process remaining content
        if after:
            self.parser.parseBlocks(parent, [after])

        return True

    def _process_nested_content(self, tag, content, blocks):
        """Process content that may contain nested tags."""
        nested_level = 1
        collected_content = []
        current_content = content
        remaining_blocks = blocks.copy()

        while nested_level > 0:
            # Process current content
            pos = 0
            while pos < len(current_content):
                # Find next start or end tag
                start_match = self.RE_START.search(current_content, pos)
                end_match = self.RE_END.search(current_content, pos)

                # No more tags found
                if not start_match and not end_match:
                    collected_content.append(current_content[pos:])
                    break

                # Determine which comes first
                if start_match and (not end_match or start_match.start() < end_match.start()):
                    # Found a start tag
                    collected_content.append(
                        current_content[pos:start_match.start()])
                    collected_content.append(start_match.group(0))
                    pos = start_match.end()
                    nested_level += 1
                else:
                    # Found an end tag
                    collected_content.append(
                        current_content[pos:end_match.start()])
                    if nested_level == 1 and end_match.group(1) == tag:
                        # This is our closing tag
                        remaining = current_content[end_match.end():]
                        if remaining.strip():
                            remaining_blocks.insert(0, remaining)
                        return ''.join(collected_content), remaining_blocks
                    nested_level -= 1
                    pos = end_match.end()

            # If we need more content and have more blocks
            if nested_level > 0 and remaining_blocks:
                current_content = remaining_blocks.pop(0)
            else:
                break

        return ''.join(collected_content), remaining_blocks

    def _handle_custom_element(self, parent, blocks, block, match, tag, attrs_string):
        """Handle custom HTML elements with nested content."""
        before = block[:match.start()]
        if before.strip():
            self.parser.parseBlocks(parent, [before])

        element = ElementTree.SubElement(parent, tag)
        self._parse_attributes(element, attrs_string)

        remaining_content = block[match.end():]
        content, remaining_blocks = self._process_nested_content(
            tag, remaining_content, blocks)

        # Clean up the content by removing end tags
        content = self._clean_end_tags(content)

        if content.strip():
            self.parser.parseChunk(element, content)

        blocks[:] = remaining_blocks
        return True

    def _clean_end_tags(self, content: str) -> str:
        """Remove end tags from the content."""
        def replace_end_tag(match):
            return ''  # Remove the end tag completely

        # Replace all end tags
        content = self.RE_END.sub(replace_end_tag, content)
        return content

    def _parse_attributes(self, element: ElementTree.Element, attrs_string: str) -> None:
        """Parse element attributes including class and ID shortcuts."""
        # Handle class attributes
        classes = [m.group(1) for m in self.RE_CLASS.finditer(attrs_string)]
        if classes:
            element.set('class', ' '.join(classes))

        # Handle ID attribute
        id_match = self.RE_ID.search(attrs_string)
        if id_match:
            element.set('id', id_match.group(1))

        # Handle other attributes
        for attr_match in self.RE_ATTR.finditer(attrs_string):
            element.set(attr_match.group(1), attr_match.group(2))


class DjangoLikeTagExtension(Extension):
    """
    Markdown extension for handling Django-like template tags.

    This extension adds support for Django-style template tags in markdown content,
    allowing both custom HTML elements and built-in Django template tags.
    """

    def extendMarkdown(self, md) -> None:
        """
        Register the Django-like tag processor with the markdown parser.

        Args:
            md: Markdown instance to extend
        """
        md.parser.blockprocessors.register(
            DjangoLikeTagProcessor(md.parser), 'django_like_tag', 175)


def makeExtension(**kwargs) -> DjangoLikeTagExtension:
    """
    Create an instance of the Django-like tag extension.

    Args:
        **kwargs: Keyword arguments for the extension

    Returns:
        DjangoLikeTagExtension: Instance of the extension
    """
    return DjangoLikeTagExtension(**kwargs)
