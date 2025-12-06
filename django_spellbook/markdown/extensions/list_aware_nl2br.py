# django_spellbook/markdown/extensions/list_aware_nl2br.py
"""
List-Aware Newline-to-Break Extension for Python-Markdown
==========================================================

This extension converts single newlines into <br/> tags (like GitHub-Flavored Markdown)
but is smart enough to NOT convert newlines that appear before list items.

This solves the common issue where lists without blank lines before them fail to render
properly when using the standard nl2br extension.

Usage:
    markdown.markdown(text, extensions=[ListAwareNl2BrExtension()])

Example:
    Input:
        ```
        Some text here.
        - List item 1
        - List item 2
        ```

    With standard nl2br: The list fails to render (becomes text with <br/> tags)
    With list_aware_nl2br: The list renders correctly as <ul><li>...</li></ul>
"""

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree
import re


class ListAwareNl2BrInlineProcessor(InlineProcessor):
    """
    Inline processor that converts newlines to <br/> tags but skips newlines
    before list markers.

    List markers supported:
    - Unordered: -, *, +
    - Ordered: 1., 2., etc.
    """

    # Pattern matches a newline that is NOT at the end of a block
    # We'll check the context in handleMatch to decide if conversion is needed
    PATTERN = r'(?<!\n)\n(?!\n)'

    # List marker patterns
    UNORDERED_LIST_MARKERS = ['-', '*', '+']
    ORDERED_LIST_PATTERN = re.compile(r'^\s*\d+\.\s')
    UNORDERED_LIST_PATTERN = re.compile(r'^\s*[-*+]\s')

    def __init__(self, md=None):
        super().__init__(self.PATTERN, md)

    def handleMatch(self, m, data):
        """
        Process a newline match. Convert to <br/> unless the next line
        starts with a list marker.

        Args:
            m: The regex match object
            data: The full text being processed

        Returns:
            (element, start, end) tuple or (None, None, None) to skip
        """
        # Get the position of the newline
        newline_pos = m.start(0)

        # Look at what comes after the newline
        text_after_newline = data[newline_pos + 1:]

        # Check if the next line starts with a list marker
        if self._is_list_marker_following(text_after_newline):
            # Don't convert this newline - let it be processed as a list
            return None, None, None

        # Convert the newline to a <br/> tag
        br = etree.Element('br')
        return br, m.start(0), m.end(0)

    def _is_list_marker_following(self, text):
        """
        Check if the text starts with a list marker (with optional whitespace).

        Args:
            text: The text to check

        Returns:
            True if text starts with a list marker, False otherwise
        """
        if not text:
            return False

        # Check for ordered list (e.g., "1. ", "  2. ")
        if self.ORDERED_LIST_PATTERN.match(text):
            return True

        # Check for unordered list (e.g., "- ", "  * ", "+ ")
        if self.UNORDERED_LIST_PATTERN.match(text):
            return True

        return False


class ListAwareNl2BrExtension(Extension):
    """
    Extension to convert newlines to <br/> tags while being aware of list syntax.

    This extension is a drop-in replacement for markdown.extensions.nl2br
    that handles lists correctly.
    """

    def extendMarkdown(self, md):
        """
        Register the list-aware nl2br processor with Markdown.

        Args:
            md: The Markdown instance
        """
        # Register with a priority of 60 to run before list processors (which have priority 90)
        # but after escape processing
        md.inlinePatterns.register(
            ListAwareNl2BrInlineProcessor(md),
            'list_aware_nl2br',
            60
        )


def makeExtension(**kwargs):
    """
    Create and return an instance of the extension.

    This function allows the extension to be loaded by name:
    markdown.markdown(text, extensions=['list_aware_nl2br'])
    """
    return ListAwareNl2BrExtension(**kwargs)
