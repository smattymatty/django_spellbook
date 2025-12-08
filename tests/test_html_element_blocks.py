"""
Tests for HTML element SpellBlocks (div, section, article, etc.)
Uses the golden file testing pattern.
"""
import unittest
import logging
from pathlib import Path
from io import StringIO
import django_spellbook
import os

from django.conf import settings
from django.test import TestCase
import django

from django_spellbook.markdown.engine import SpellbookMarkdownEngine
from django_spellbook.blocks import SpellBlockRegistry
from django_spellbook.spellblocks import (
    HTMLElementBlock,
    DivBlock, SectionBlock, ArticleBlock, AsideBlock,
    HeaderBlock, FooterBlock, NavBlock, MainBlock,
    HrBlock, BrBlock
)
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

# --- Constants for File Paths ---
BASE_TEST_DIR = Path(__file__).parent
HTML_ELEMENTS_INPUT_MD_DIR = BASE_TEST_DIR / 'markdown_testers' / 'html_elements'
HTML_ELEMENTS_OUTPUT_HTML_DIR = BASE_TEST_DIR / 'html_testers' / 'html_elements'
HTML_ELEMENTS_GOLDEN_HTML_DIR = BASE_TEST_DIR / 'html_goldens' / 'html_elements'


class TestHTMLElementBlocks(TestCase):
    """
    Integration tests for HTML element SpellBlocks using the SpellbookMarkdownEngine.
    Uses golden file pattern for comparing rendered output.
    """
    engine = None
    reporter_buffer = None
    reporter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_templates_dir = BASE_TEST_DIR / "templates"

        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django_spellbook',
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                ],
                TEMPLATES=[
                    {
                        'BACKEND': 'django.template.backends.django.DjangoTemplates',
                        'DIRS': [
                            str(cls.test_templates_dir),
                            str(Path(django_spellbook.__file__).parent / 'templates')
                        ],
                        'APP_DIRS': True,
                        'OPTIONS': {
                            'debug': True,
                            'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                            ],
                            'builtins': [
                                'django_spellbook.templatetags.spellbook_tags',
                            ]
                        },
                    }
                ],
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                },
            )
            django.setup()

        # Prepare directories
        os.makedirs(HTML_ELEMENTS_INPUT_MD_DIR, exist_ok=True)
        os.makedirs(HTML_ELEMENTS_OUTPUT_HTML_DIR, exist_ok=True)
        os.makedirs(HTML_ELEMENTS_GOLDEN_HTML_DIR, exist_ok=True)

    def _clear_and_register_html_element_blocks(self):
        """Clears the registry and registers only HTML element blocks."""
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        else:
            SpellBlockRegistry.blocks = {}

        # Register all HTML element blocks
        html_blocks = [
            DivBlock, SectionBlock, ArticleBlock, AsideBlock,
            HeaderBlock, FooterBlock, NavBlock, MainBlock,
            HrBlock, BrBlock
        ]

        for block_class in html_blocks:
            if hasattr(block_class, 'name') and block_class.name:
                SpellBlockRegistry._registry[block_class.name] = block_class
            else:
                raise ValueError(f"{block_class.__name__} must have a 'name' attribute for registration.")

    def setUp(self):
        """Set up for each test method."""
        self._clear_and_register_html_element_blocks()

        self.reporter_buffer = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_buffer, report_level='debug')
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)

    def _normalize_html(self, html_content):
        """Normalizes HTML content for comparison."""
        return html_content.strip()

    def _run_html_element_test(self, md_filename_stem):
        """
        Helper method: reads MD, renders, and compares against golden HTML.
        md_filename_stem is the name without the .md extension.
        """
        md_filename = f"{md_filename_stem}.md"
        golden_html_filename = f"{md_filename_stem}.html"

        input_md_path = HTML_ELEMENTS_INPUT_MD_DIR / md_filename
        golden_html_path = HTML_ELEMENTS_GOLDEN_HTML_DIR / golden_html_filename
        output_html_path = HTML_ELEMENTS_OUTPUT_HTML_DIR / f"output_{golden_html_filename}"

        self.assertTrue(input_md_path.exists(), f"Markdown input file not found: {input_md_path}")

        with open(input_md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        actual_html = self.engine.parse_and_render(markdown_text)

        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(actual_html)

        if not golden_html_path.exists():
            os.makedirs(golden_html_path.parent, exist_ok=True)
            normalized_for_golden_creation = self._normalize_html(actual_html)
            with open(golden_html_path, 'w', encoding='utf-8') as f:
                f.write(normalized_for_golden_creation)
            self.fail(f"Golden HTML file was missing, CREATED: {golden_html_path}. "
                      f"Manually verify its content and re-run the test.")

        with open(golden_html_path, 'r', encoding='utf-8') as f:
            expected_html_raw = f.read()

        normalized_actual_html = self._normalize_html(actual_html)
        normalized_expected_html = self._normalize_html(expected_html_raw)

        self.assertMultiLineEqual(
            normalized_actual_html,
            normalized_expected_html,
            f"Normalized HTML for {md_filename} does not match golden file {golden_html_filename}.\n"
            f"Actual raw output saved to: {output_html_path}\n"
            f"Reporter output (if any errors/warnings occurred):\n{self.reporter_buffer.getvalue()}"
        )

    # --- Test Methods for Div Block ---

    def test_div_basic(self):
        """Test basic div rendering"""
        self._run_html_element_test("div_basic")

    def test_div_with_single_class(self):
        """Test div with single class"""
        self._run_html_element_test("div_single_class")

    def test_div_with_multiple_classes(self):
        """Test div with multiple classes"""
        self._run_html_element_test("div_multiple_classes")

    def test_div_with_id(self):
        """Test div with ID"""
        self._run_html_element_test("div_with_id")

    def test_div_with_class_and_id(self):
        """Test div with class and ID"""
        self._run_html_element_test("div_class_and_id")

    def test_div_with_htmx_attributes(self):
        """Test div with HTMX attributes"""
        self._run_html_element_test("div_htmx")

    def test_div_with_data_attributes(self):
        """Test div with data attributes"""
        self._run_html_element_test("div_data_attrs")

    # --- Test Methods for Other Block Elements ---

    def test_section_basic(self):
        """Test section element"""
        self._run_html_element_test("section_basic")

    def test_article_basic(self):
        """Test article element"""
        self._run_html_element_test("article_basic")

    def test_aside_basic(self):
        """Test aside element"""
        self._run_html_element_test("aside_basic")

    def test_header_basic(self):
        """Test header element"""
        self._run_html_element_test("header_basic")

    def test_footer_basic(self):
        """Test footer element"""
        self._run_html_element_test("footer_basic")

    def test_nav_basic(self):
        """Test nav element"""
        self._run_html_element_test("nav_basic")

    def test_main_basic(self):
        """Test main element"""
        self._run_html_element_test("main_basic")

    # --- Test Methods for Void Elements ---

    def test_hr_basic(self):
        """Test basic hr element"""
        self._run_html_element_test("hr_basic")

    def test_hr_with_class(self):
        """Test hr element with class"""
        self._run_html_element_test("hr_with_class")

    def test_br_basic(self):
        """Test basic br element"""
        self._run_html_element_test("br_basic")

    def test_br_with_class(self):
        """Test br element with class"""
        self._run_html_element_test("br_with_class")


class TestHTMLElementBlockBase(TestCase):
    """Unit tests for the HTMLElementBlock base class"""

    def setUp(self):
        self.reporter = MarkdownReporter(StringIO(), report_level='minimal')

    def test_tag_name_required(self):
        """Test that tag_name must be defined"""
        block = HTMLElementBlock(
            reporter=self.reporter,
            content='test'
        )
        with self.assertRaises(ValueError):
            block.get_context()

    def test_void_element_with_content_logs_error(self):
        """Test that void element with content logs error"""
        class TestVoidBlock(HTMLElementBlock):
            tag_name = 'test-void'
            is_void = True

        block = TestVoidBlock(
            reporter=self.reporter,
            content='This should not be here'
        )

        context = block.get_context()
        self.assertEqual(context['content'], '')
        self.assertTrue(context['is_void'])


if __name__ == '__main__':
    unittest.main()
