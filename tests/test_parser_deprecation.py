"""
Tests for parser function deprecation.

This module tests the soft deprecation of render_spellbook_markdown_to_html
in favor of the new spellbook_render function.
"""

import warnings
from django.test import TestCase
from django_spellbook.parsers import spellbook_render, render_spellbook_markdown_to_html


class TestParserDeprecation(TestCase):
    """Test deprecation of old parser function name."""

    def test_new_function_works(self):
        """Test that spellbook_render works correctly."""
        markdown = "# Hello World\n\nThis is a test."
        html = spellbook_render(markdown)

        self.assertIn("Hello World", html)
        self.assertIn("This is a test.", html)
        self.assertIn("<h1", html)  # Has heading tag

    def test_old_function_still_works(self):
        """Test that deprecated function still returns correct output."""
        markdown = "# Hello World\n\nThis is a test."

        # Suppress the deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            html = render_spellbook_markdown_to_html(markdown)

        self.assertIn("Hello World", html)
        self.assertIn("This is a test.", html)
        self.assertIn("<h1", html)  # Has heading tag

    def test_old_function_emits_deprecation_warning(self):
        """Test that deprecated function emits DeprecationWarning."""
        markdown = "# Test"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            html = render_spellbook_markdown_to_html(markdown)

            # Should have exactly one warning
            self.assertEqual(len(w), 1)

            # Should be a DeprecationWarning
            self.assertEqual(w[0].category, DeprecationWarning)

            # Check warning message content
            message = str(w[0].message)
            self.assertIn("render_spellbook_markdown_to_html", message)
            self.assertIn("deprecated", message)
            self.assertIn("spellbook_render", message)
            self.assertIn("0.4.0", message)

    def test_warning_points_to_caller(self):
        """Test that deprecation warning has correct stacklevel."""
        markdown = "# Test"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Call from this line - warning should point here
            html = render_spellbook_markdown_to_html(markdown)

            # Verify warning was raised
            self.assertEqual(len(w), 1)

            # The warning should point to this test file, not parsers.py
            self.assertIn("test_parser_deprecation.py", w[0].filename)

    def test_both_functions_produce_same_output(self):
        """Test that both functions produce identical output."""
        markdown = """
# Heading

Some **bold** and *italic* text.

- List item 1
- List item 2

{~ alert type="info" ~}
This is an alert.
{~~}
"""

        # New function
        new_html = spellbook_render(markdown)

        # Old function (suppress warning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old_html = render_spellbook_markdown_to_html(markdown)

        # Both should produce identical output
        self.assertEqual(new_html, old_html)

    def test_new_function_with_reporter(self):
        """Test that spellbook_render works with reporter argument."""
        from io import StringIO
        from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

        markdown = "# Test"
        reporter = MarkdownReporter(StringIO(), report_level='debug')

        html = spellbook_render(markdown, reporter=reporter)
        self.assertIn("Test", html)
        self.assertIn("<h1", html)

    def test_old_function_with_reporter(self):
        """Test that deprecated function still works with reporter argument."""
        from io import StringIO
        from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

        markdown = "# Test"
        reporter = MarkdownReporter(StringIO(), report_level='debug')

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            html = render_spellbook_markdown_to_html(markdown, reporter=reporter)

        self.assertIn("Test", html)
        self.assertIn("<h1", html)

    def test_warning_message_format(self):
        """Test that warning message is clear and actionable."""
        markdown = "# Test"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            html = render_spellbook_markdown_to_html(markdown)

            message = str(w[0].message)

            # Should mention what's deprecated
            self.assertIn("render_spellbook_markdown_to_html", message)

            # Should mention it's deprecated
            self.assertIn("deprecated", message.lower())

            # Should mention what to use instead
            self.assertIn("spellbook_render", message)

            # Should mention when it will be removed
            self.assertIn("0.4.0", message)

            # Should be clear about the action ("Use X instead")
            self.assertIn("Use", message)
            self.assertIn("instead", message)
