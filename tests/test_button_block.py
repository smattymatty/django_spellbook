import unittest
import logging
from pathlib import Path
from io import StringIO
import django_spellbook
import os
import re 

from django.conf import settings
from django.test import TestCase
import django

from django_spellbook.parsers import spellbook_render
from django_spellbook.blocks import SpellBlockRegistry
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

from django_spellbook.spellblocks import ButtonBlock


# --- Constants for File Paths ---
BASE_TEST_DIR = Path(__file__).parent
BUTTON_BLOCK_INPUT_MD_DIR = BASE_TEST_DIR / 'markdown_testers' / 'button_block'
BUTTON_BLOCK_OUTPUT_HTML_DIR = BASE_TEST_DIR / 'html_testers' / 'button_block'
BUTTON_BLOCK_GOLDEN_HTML_DIR = BASE_TEST_DIR / 'html_goldens' / 'button_block'

# Optional: Keep logging disabled for cleaner test output
# logging.disable(logging.CRITICAL)

class TestButtonBlockIntegration(TestCase):
    """
    Integration tests for the ButtonBlock using the SpellbookMarkdownEngine.
    Focuses on rendering various configurations of the button block
    and comparing against golden HTML files.
    """
    engine = None
    reporter_buffer = None
    reporter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_templates_dir = BASE_TEST_DIR / "templates" # For any test-specific general templates

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

        # Prepare directories for button block tests
        os.makedirs(BUTTON_BLOCK_INPUT_MD_DIR, exist_ok=True)
        os.makedirs(BUTTON_BLOCK_OUTPUT_HTML_DIR, exist_ok=True)
        os.makedirs(BUTTON_BLOCK_GOLDEN_HTML_DIR, exist_ok=True)

    def _clear_and_register_button_block(self):
        """Clears the registry and registers only the ButtonBlock."""
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        else:
            print("Warning: Could not directly clear SpellBlockRegistry._registry. Attempting alternative.")
            SpellBlockRegistry.blocks = {}

        if hasattr(ButtonBlock, 'name') and ButtonBlock.name:
            SpellBlockRegistry._registry[ButtonBlock.name] = ButtonBlock
        else:
            raise ValueError("ButtonBlock must have a 'name' attribute for registration.")

    def setUp(self):
        """Set up for each test method."""
        self._clear_and_register_button_block()

        self.reporter_buffer = StringIO()

    def _normalize_html(self, html_content):
        """
        Normalizes HTML content for comparison.
        Strips leading/trailing whitespace.
        """
        # Add more complex normalization if attribute order or minor whitespace causes issues.
        # For buttons, class order might vary if generated dynamically but should be fine.
        html_content = html_content.strip()
        # Example: Replace multiple spaces with single space within tags if that's an issue
        # html_content = re.sub(r'\s+', ' ', html_content)
        return html_content

    def _run_button_block_test(self, md_filename_stem):
        """
        Helper method for ButtonBlock: reads MD, renders, and compares against golden HTML.
        """
        md_filename = f"{md_filename_stem}.md"
        golden_html_filename = f"{md_filename_stem}.html"

        input_md_path = BUTTON_BLOCK_INPUT_MD_DIR / md_filename
        golden_html_path = BUTTON_BLOCK_GOLDEN_HTML_DIR / golden_html_filename
        output_html_path = BUTTON_BLOCK_OUTPUT_HTML_DIR / f"output_{golden_html_filename}"

        self.assertTrue(input_md_path.exists(), f"Markdown input file not found: {input_md_path}")

        with open(input_md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        actual_html = spellbook_render(markdown_text)

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

    # --- Test Methods for ButtonSpellBlock ---

    def test_button_default_link(self):
        """Test ButtonBlock with minimal href and label."""
        self._run_button_block_test("button_default_link")

    def test_button_primary_large(self):
        """Test ButtonBlock with type='primary' and size='lg'."""
        self._run_button_block_test("button_primary_large")

    def test_button_secondary_small_new_tab(self):
        """Test ButtonBlock with type='secondary', size='sm', and target='_blank'."""
        self._run_button_block_test("button_secondary_small_new_tab")

    def test_button_with_icon_left(self):
        """Test ButtonBlock with icon_left."""
        self._run_button_block_test("button_with_icon_left")

    def test_button_with_icon_right(self):
        """Test ButtonBlock with icon_right."""
        self._run_button_block_test("button_with_icon_right")

    def test_button_with_both_icons(self):
        """Test ButtonBlock with both icon_left and icon_right."""
        self._run_button_block_test("button_with_both_icons")

    def test_button_disabled(self):
        """Test ButtonBlock with disabled='true'."""
        self._run_button_block_test("button_disabled")

    def test_button_custom_class_and_id(self):
        """Test ButtonBlock with custom 'class' and 'id' attributes."""
        self._run_button_block_test("button_custom_class_and_id")

    def test_button_no_href_fallback(self):
        """Test ButtonBlock when href is omitted (should fallback to '#')."""
        self._run_button_block_test("button_no_href_fallback")

    def test_button_all_params_link(self):
        """Test a link button with many parameters set."""
        self._run_button_block_test("button_all_params_link")
        
    def test_button_different_types_and_sizes(self):
        """Test various combinations of types and sizes (can be one MD file with multiple buttons)."""
        self._run_button_block_test("button_various_types_sizes")
    
    def test_button_different_types_and_sizes(self):
        """Test various combinations of types and sizes (can be one MD file with multiple buttons)."""
        self._run_button_block_test("docs_examples")

# If you add complex helper methods to ButtonBlock's Python code later,
# you might consider a separate class similar to TestProcessDimensionValue.

if __name__ == '__main__':
    # This allows running the tests directly from this file.
    # Ensure Django settings are configured if run this way outside of manage.py test.
    # The setUpClass handles basic configuration.
    unittest.main()