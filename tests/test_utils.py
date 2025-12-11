from django.test import TestCase
import re
from io import StringIO

from django_spellbook.utils import remove_leading_dash, titlefy
from django_spellbook.parsers import spellbook_render
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter


# ============================================================================
# Test Helper Functions
# ============================================================================

def normalize_html(html_str):
    """
    Normalize HTML for comparison by removing extra whitespace and formatting.

    Args:
        html_str: HTML string to normalize

    Returns:
        Normalized HTML string
    """
    # Remove newlines and extra spaces
    html = re.sub(r'\s+', ' ', html_str)
    # Remove spaces around tags
    html = re.sub(r'>\s+<', '><', html)
    # Strip leading/trailing whitespace
    html = html.strip()
    return html


def assert_html_equal(actual, expected, msg=None):
    """
    Assert that two HTML strings are equal after normalization.

    Args:
        actual: Actual HTML string
        expected: Expected HTML string
        msg: Optional message for assertion error
    """
    normalized_actual = normalize_html(actual)
    normalized_expected = normalize_html(expected)

    if normalized_actual != normalized_expected:
        error_msg = msg or f"\nActual:\n{normalized_actual}\n\nExpected:\n{normalized_expected}"
        raise AssertionError(error_msg)


def render_markdown(markdown_str, reporter=None):
    """
    Helper to render markdown using SpellbookMarkdownEngine.

    Args:
        markdown_str: Markdown string to render
        reporter: Optional MarkdownReporter instance

    Returns:
        Rendered HTML string
    """
    if reporter is None:
        reporter = MarkdownReporter(
            stdout=StringIO(),
            report_level='minimal'
        )

    return spellbook_render(markdown_str, reporter)


# ============================================================================
# Tests
# ============================================================================

class TestUtils(TestCase):
    def test_remove_leading_dash(self):
        """Test removing leading dashes from a string"""
        result = remove_leading_dash('--test')
        self.assertEqual(result, 'test')

    def test_titlefy(self):
        """Test titlefy function"""
        result = titlefy('test-page')
        self.assertEqual(result, 'Test Page')
        result = titlefy('this-is-a-test-page')
        self.assertEqual(result, 'This is a Test Page')

    def test_titlefy_without_dashes(self):
        """Test titlefy function without dashes"""
        result = titlefy('test page')
        self.assertEqual(result, 'Test Page')


class TestHtmlTestHelpers(TestCase):
    """Tests for the HTML testing helper functions"""

    def test_normalize_html_removes_whitespace(self):
        """Test that normalize_html removes extra whitespace"""
        html = """
        <div class="test">
            <p>Content</p>
        </div>
        """
        normalized = normalize_html(html)
        self.assertEqual(normalized, '<div class="test"><p>Content</p></div>')

    def test_normalize_html_strips_edges(self):
        """Test that normalize_html strips leading/trailing whitespace"""
        html = "   <div>test</div>   "
        normalized = normalize_html(html)
        self.assertEqual(normalized, '<div>test</div>')

    def test_assert_html_equal_passes_when_equal(self):
        """Test that assert_html_equal passes for equivalent HTML"""
        html1 = "<div class='test'><p>Content</p></div>"
        html2 = """
        <div class='test'>
            <p>Content</p>
        </div>
        """
        # Should not raise
        assert_html_equal(html1, html2)

    def test_assert_html_equal_fails_when_different(self):
        """Test that assert_html_equal fails for different HTML"""
        html1 = "<div>test1</div>"
        html2 = "<div>test2</div>"

        with self.assertRaises(AssertionError):
            assert_html_equal(html1, html2)
