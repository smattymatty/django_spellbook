"""
Tests for the enhanced attribute parser with shorthand syntax support.
"""
from django.test import TestCase
from io import StringIO

from django_spellbook.markdown.attribute_parser import (
    parse_shorthand_and_explicit_attributes,
    parse_spellblock_style_attributes,
)
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter


class TestShorthandSyntax(TestCase):
    """Test shorthand syntax parsing (.class, #id)"""

    def test_single_class(self):
        """Test parsing a single class"""
        result = parse_shorthand_and_explicit_attributes('.my-class')
        self.assertEqual(result, {'class': 'my-class'})

    def test_multiple_classes(self):
        """Test parsing multiple classes"""
        result = parse_shorthand_and_explicit_attributes('.class1 .class2 .class3')
        self.assertEqual(result, {'class': 'class1 class2 class3'})

    def test_single_id(self):
        """Test parsing a single ID"""
        result = parse_shorthand_and_explicit_attributes('#my-id')
        self.assertEqual(result, {'id': 'my-id'})

    def test_class_and_id(self):
        """Test parsing class and ID together"""
        result = parse_shorthand_and_explicit_attributes('.my-class #my-id')
        self.assertEqual(result, {'class': 'my-class', 'id': 'my-id'})

    def test_multiple_classes_and_id(self):
        """Test parsing multiple classes and ID"""
        result = parse_shorthand_and_explicit_attributes('.c1 .c2 #my-id')
        self.assertEqual(result, {'class': 'c1 c2', 'id': 'my-id'})

    def test_hyphenated_class_names(self):
        """Test that hyphenated class names work"""
        result = parse_shorthand_and_explicit_attributes('.my-long-class-name')
        self.assertEqual(result, {'class': 'my-long-class-name'})

    def test_hyphenated_id_names(self):
        """Test that hyphenated ID names work"""
        result = parse_shorthand_and_explicit_attributes('#my-long-id')
        self.assertEqual(result, {'id': 'my-long-id'})


class TestExplicitSyntax(TestCase):
    """Test explicit attribute syntax (key="value")"""

    def test_double_quoted_value(self):
        """Test parsing double-quoted attribute values"""
        result = parse_shorthand_and_explicit_attributes('class="my-class"')
        self.assertEqual(result, {'class': 'my-class'})

    def test_single_quoted_value(self):
        """Test parsing single-quoted attribute values"""
        result = parse_shorthand_and_explicit_attributes("class='my-class'")
        self.assertEqual(result, {'class': 'my-class'})

    def test_unquoted_value(self):
        """Test parsing unquoted attribute values"""
        result = parse_shorthand_and_explicit_attributes('id=my-id')
        self.assertEqual(result, {'id': 'my-id'})

    def test_multiple_attributes(self):
        """Test parsing multiple explicit attributes"""
        result = parse_shorthand_and_explicit_attributes('class="test" id="my-id"')
        self.assertEqual(result, {'class': 'test', 'id': 'my-id'})

    def test_empty_string_value(self):
        """Test parsing empty string values"""
        result = parse_shorthand_and_explicit_attributes('data-value=""')
        self.assertEqual(result, {'data-value': ''})

    def test_boolean_flag(self):
        """Test parsing boolean flags (no value)"""
        result = parse_shorthand_and_explicit_attributes('disabled')
        self.assertEqual(result, {'disabled': 'disabled'})


class TestHyphenatedAttributes(TestCase):
    """Test hyphenated attribute names (hx-*, data-*, aria-*)"""

    def test_htmx_attributes(self):
        """Test HTMX attribute parsing"""
        result = parse_shorthand_and_explicit_attributes('hx-get="/api" hx-target="#result"')
        self.assertEqual(result, {'hx-get': '/api', 'hx-target': '#result'})

    def test_data_attributes(self):
        """Test data-* attribute parsing"""
        result = parse_shorthand_and_explicit_attributes('data-id="123" data-name="test"')
        self.assertEqual(result, {'data-id': '123', 'data-name': 'test'})

    def test_aria_attributes(self):
        """Test ARIA attribute parsing"""
        result = parse_shorthand_and_explicit_attributes('aria-label="My Label" aria-hidden="true"')
        self.assertEqual(result, {'aria-label': 'My Label', 'aria-hidden': 'true'})

    def test_mixed_hyphenated_attributes(self):
        """Test mixing different types of hyphenated attributes"""
        result = parse_shorthand_and_explicit_attributes(
            'hx-get="/api" data-id="123" aria-label="Test"'
        )
        self.assertEqual(result, {
            'hx-get': '/api',
            'data-id': '123',
            'aria-label': 'Test'
        })


class TestAttributeMerging(TestCase):
    """Test merging of shorthand and explicit attributes"""

    def test_shorthand_class_before_explicit_class(self):
        """Test that shorthand classes come before explicit classes"""
        result = parse_shorthand_and_explicit_attributes('.c1 class="c2"')
        self.assertEqual(result, {'class': 'c1 c2'})

    def test_explicit_class_after_shorthand_class(self):
        """Test that explicit classes append to shorthand classes"""
        result = parse_shorthand_and_explicit_attributes('class="c1" .c2')
        self.assertEqual(result, {'class': 'c2 c1'})

    def test_multiple_shorthand_and_explicit_classes(self):
        """Test merging multiple shorthand and explicit classes"""
        result = parse_shorthand_and_explicit_attributes('.c1 .c2 class="c3 c4"')
        self.assertEqual(result, {'class': 'c1 c2 c3 c4'})

    def test_duplicate_classes_removed(self):
        """Test that duplicate classes are removed while preserving order"""
        result = parse_shorthand_and_explicit_attributes('.c1 .c2 class="c1 c3"')
        self.assertEqual(result, {'class': 'c1 c2 c3'})

    def test_explicit_id_overrides_shorthand_id(self):
        """Test that explicit ID overrides shorthand ID"""
        reporter = MarkdownReporter(StringIO(), report_level='minimal')
        result = parse_shorthand_and_explicit_attributes('#shorthand id="explicit"', reporter)
        self.assertEqual(result, {'id': 'explicit'})

    def test_shorthand_id_used_when_no_explicit(self):
        """Test that shorthand ID is used when no explicit ID present"""
        result = parse_shorthand_and_explicit_attributes('#my-id class="test"')
        self.assertEqual(result, {'id': 'my-id', 'class': 'test'})


class TestComplexCombinations(TestCase):
    """Test complex combinations of shorthand and explicit attributes"""

    def test_htmx_with_shorthand(self):
        """Test HTMX attributes combined with shorthand syntax"""
        result = parse_shorthand_and_explicit_attributes(
            '.btn .primary #submit-btn hx-post="/submit" hx-target="#result"'
        )
        self.assertEqual(result, {
            'class': 'btn primary',
            'id': 'submit-btn',
            'hx-post': '/submit',
            'hx-target': '#result'
        })

    def test_everything_combined(self):
        """Test combining shorthand, explicit, data, HTMX, and ARIA attributes"""
        result = parse_shorthand_and_explicit_attributes(
            '.container #main data-section="hero" '
            'hx-get="/content" aria-label="Main content" '
            'role="main"'
        )
        self.assertEqual(result, {
            'class': 'container',
            'id': 'main',
            'data-section': 'hero',
            'hx-get': '/content',
            'aria-label': 'Main content',
            'role': 'main'
        })

    def test_alpine_js_attributes(self):
        """Test Alpine.js-style attributes"""
        result = parse_shorthand_and_explicit_attributes(
            '.modal x-data="{open:false}" x-show="open" @click="open=true"'
        )
        self.assertEqual(result, {
            'class': 'modal',
            'x-data': '{open:false}',
            'x-show': 'open',
            '@click': 'open=true'
        })


class TestEdgeCases(TestCase):
    """Test edge cases and error handling"""

    def test_empty_string(self):
        """Test parsing empty string"""
        result = parse_shorthand_and_explicit_attributes('')
        self.assertEqual(result, {})

    def test_whitespace_only(self):
        """Test parsing whitespace-only string"""
        result = parse_shorthand_and_explicit_attributes('   ')
        self.assertEqual(result, {})

    def test_none_input(self):
        """Test parsing None input"""
        result = parse_shorthand_and_explicit_attributes(None)
        self.assertEqual(result, {})

    def test_multiple_ids_explicit_wins(self):
        """Test that with multiple IDs, explicit wins"""
        reporter = MarkdownReporter(StringIO(), report_level='minimal')
        result = parse_shorthand_and_explicit_attributes('#id1 id="id2"', reporter)
        self.assertEqual(result['id'], 'id2')

    def test_class_with_special_characters(self):
        """Test classes with allowed special characters"""
        result = parse_shorthand_and_explicit_attributes('.test:hover')
        self.assertEqual(result, {'class': 'test:hover'})


class TestBackwardCompatibility(TestCase):
    """Test that parse_spellblock_style_attributes still works"""

    def test_parse_spellbook_style_attributes_wrapper(self):
        """Test that the old function name still works"""
        result = parse_spellblock_style_attributes('.my-class #my-id')
        self.assertEqual(result, {'class': 'my-class', 'id': 'my-id'})

    def test_explicit_only_still_works(self):
        """Test that explicit-only syntax still works"""
        result = parse_spellblock_style_attributes('type="warning" dismissible="true"')
        self.assertEqual(result, {'type': 'warning', 'dismissible': 'true'})
