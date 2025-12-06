# django_spellbook/markdown/preprocessors/list_fixer.py
"""
List Fixer Preprocessor for Python-Markdown
============================================

This preprocessor automatically adds blank lines before list items that don't have them,
allowing GitHub-Flavored Markdown style lists without requiring blank lines.

Example transformation:
    Input:
        ```
        Some text here:
        - List item 1
        - List item 2
        ```

    Output:
        ```
        Some text here:

        - List item 1
        - List item 2
        ```

This allows lists to render correctly even when the author doesn't add blank lines.
"""

from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension
import re


class ListFixerPreprocessor(Preprocessor):
    """
    Preprocessor that adds blank lines before list items.

    This runs before the markdown parser, modifying the raw text to ensure
    lists are properly detected by adding blank lines where needed.
    """

    # Pattern to match list markers at the start of a line
    # Matches: "- ", "* ", "+ ", "1. ", "2. ", etc.
    LIST_MARKER_PATTERN = re.compile(r'^(\s*)([-*+]|\d+\.)\s', re.MULTILINE)

    def run(self, lines):
        """
        Process the lines and add blank lines before lists.

        Args:
            lines: List of strings (lines of markdown text)

        Returns:
            List of strings with blank lines added before lists
        """
        if not lines:
            return lines

        result = []
        i = 0

        while i < len(lines):
            current_line = lines[i]

            # Check if this line starts a list
            if self._is_list_start(current_line):
                # Check if the previous line exists and is not blank
                if result and result[-1].strip():
                    # Add a blank line before the list
                    result.append('')

            result.append(current_line)
            i += 1

        return result

    def _is_list_start(self, line):
        """
        Check if a line starts with a list marker.

        Args:
            line: The line to check

        Returns:
            True if the line starts with a list marker, False otherwise
        """
        # Match unordered lists: "- ", "* ", "+ "
        # Match ordered lists: "1. ", "2. ", etc.
        # Allow optional leading whitespace for indented lists
        return bool(self.LIST_MARKER_PATTERN.match(line))


class ListFixerExtension(Extension):
    """
    Extension that registers the ListFixerPreprocessor.
    """

    def extendMarkdown(self, md):
        """
        Register the preprocessor with Markdown.

        Args:
            md: The Markdown instance
        """
        # Register with priority 25 (runs early, before most other preprocessors)
        md.preprocessors.register(
            ListFixerPreprocessor(md),
            'list_fixer',
            25
        )


def makeExtension(**kwargs):
    """
    Create and return an instance of the extension.

    This function allows the extension to be loaded by name:
    markdown.markdown(text, extensions=['list_fixer'])
    """
    return ListFixerExtension(**kwargs)
