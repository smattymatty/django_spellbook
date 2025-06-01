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
from django_spellbook.spellblocks import AlignBlock

# Assuming the reporter path is standard for your project
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

# --- Constants for File Paths ---
BASE_TEST_DIR = Path(__file__).parent
ALIGN_BLOCK_INPUT_MD_DIR = BASE_TEST_DIR / 'markdown_testers' / 'align_block'
ALIGN_BLOCK_OUTPUT_HTML_DIR = BASE_TEST_DIR / 'html_testers' / 'align_block' # Test-generated output
ALIGN_BLOCK_GOLDEN_HTML_DIR = BASE_TEST_DIR / 'html_goldens' / 'align_block' # Expected correct output

# Optional: Keep logging disabled for cleaner test output
# logging.disable(logging.CRITICAL)

class TestAlignBlockIntegration(TestCase):
    """
    Integration tests for the AlignBlock using the SpellbookMarkdownEngine.
    Focuses on rendering various configurations of the align block
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
                    'django_spellbook', # Your app
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                ],
                TEMPLATES=[
                    {
                        'BACKEND': 'django.template.backends.django.DjangoTemplates',
                        # Ensure align.html (django_spellbook/blocks/align.html) can be found
                        'DIRS': [
                            str(cls.test_templates_dir), # For test-specific overrides/additions
                            str(Path(django_spellbook.__file__).parent / 'templates') # Main app templates
                        ],
                        'APP_DIRS': True, # Checks app/templates directories
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

        # Prepare directories for align block tests
        os.makedirs(ALIGN_BLOCK_INPUT_MD_DIR, exist_ok=True) # Create if they don't exist
        os.makedirs(ALIGN_BLOCK_OUTPUT_HTML_DIR, exist_ok=True)
        os.makedirs(ALIGN_BLOCK_GOLDEN_HTML_DIR, exist_ok=True)

    def _clear_and_register_align_block(self):
        """Clears the registry and registers only the AlignBlock."""
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        else:
            # Fallback or warning if clearing mechanism is different
            # This might happen if SpellBlockRegistry's implementation changes
            print("Warning: Could not directly clear SpellBlockRegistry._registry. Attempting alternative.")
            SpellBlockRegistry.blocks = {} # Assuming 'blocks' might be the dict

        # Ensure AlignBlock has a 'name' attribute as expected by the registration process
        if hasattr(AlignBlock, 'name') and AlignBlock.name:
            SpellBlockRegistry._registry[AlignBlock.name] = AlignBlock
        else:
            raise ValueError("AlignBlock must have a 'name' attribute for registration.")

    def setUp(self):
        """Set up for each test method."""
        self._clear_and_register_align_block()

        self.reporter_buffer = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_buffer, report_level='debug')
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)

    def _normalize_html(self, html_content):
        """
        Normalizes HTML content for comparison.
        Strips leading/trailing whitespace. Add more normalization if needed
        (e.g., for dynamic IDs, attribute order, etc.).
        """
        # Example: remove whitespace between tags to reduce trivial differences
        # html_content = re.sub(r'>\s+<', '><', html_content)
        # Example: sort class names if order isn't guaranteed
        # def sort_classes(match):
        #     attrs = match.group(1)
        #     parts = attrs.split('class="')
        #     if len(parts) > 1:
        #         pre_class = parts[0]
        #         class_val_and_post = parts[1].split('"')
        #         class_val = class_val_and_post[0]
        #         post_class = '"'.join(class_val_and_post[1:])
        #         sorted_classes = " ".join(sorted(class_val.split()))
        #         return f'{pre_class}class="{sorted_classes}"{post_class}'
        #     return attrs
        # html_content = re.sub(r'(<[a-zA-Z0-9]+\s+[^>]*?)>', sort_classes, html_content)
        return html_content.strip()

    def _run_align_block_test(self, md_filename_stem):
        """
        Helper method for AlignBlock: reads MD, renders, and compares against golden HTML.
        md_filename_stem is the name without the .md extension.
        """
        md_filename = f"{md_filename_stem}.md"
        golden_html_filename = f"{md_filename_stem}.html"

        input_md_path = ALIGN_BLOCK_INPUT_MD_DIR / md_filename
        golden_html_path = ALIGN_BLOCK_GOLDEN_HTML_DIR / golden_html_filename
        # Save actual output for debugging purposes
        output_html_path = ALIGN_BLOCK_OUTPUT_HTML_DIR / f"output_{golden_html_filename}"

        self.assertTrue(input_md_path.exists(), f"Markdown input file not found: {input_md_path}")

        with open(input_md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        actual_html = self.engine.parse_and_render(markdown_text)

        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(actual_html)

        if not golden_html_path.exists():
            # If golden file is missing, create it from the current output for review.
            os.makedirs(golden_html_path.parent, exist_ok=True) # Ensure directory exists
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

    # --- Test Methods for AlignSpellBlock ---

    def test_align_block_default_values(self):
        """Test AlignBlock with no parameters (should use defaults)."""
        self._run_align_block_test("align_default_values")

    def test_align_block_pos_start(self):
        """Test AlignBlock with pos='start'."""
        self._run_align_block_test("align_pos_start")

    def test_align_block_pos_center(self):
        """Test AlignBlock with pos='center'."""
        self._run_align_block_test("align_pos_center")

    def test_align_block_pos_end(self):
        """Test AlignBlock with pos='end'."""
        self._run_align_block_test("align_pos_end")

    def test_align_block_width_50_percent(self):
        """Test AlignBlock with width='50%'."""
        self._run_align_block_test("align_width_50_percent")

    def test_align_block_height_explicit_value(self):
        """Test AlignBlock with an explicit height (e.g., height='200px').
           Note: AlignBlock Python needs to support units other than % for this to be meaningful,
           or template needs to handle it. Assuming current implementation passes it through."""
        # If your AlignBlock only supports % or 'auto' for height, adjust md or Python.
        self._run_align_block_test("align_height_200px") # md would be: {~ align height="200px" ~}..

    def test_align_block_width_auto_height_auto(self):
        """Test AlignBlock with width='auto' and height='auto'."""
        self._run_align_block_test("align_width_auto_height_auto")

    def test_align_block_content_align_start(self):
        """Test AlignBlock with content_align='start'."""
        self._run_align_block_test("align_content_align_start")

    def test_align_block_content_align_center(self):
        """Test AlignBlock with content_align='center'."""
        self._run_align_block_test("align_content_align_center")

    def test_align_block_content_align_end(self):
        """Test AlignBlock with content_align='end'."""
        self._run_align_block_test("align_content_align_end")

    def test_align_block_custom_classes_and_id(self):
        """Test AlignBlock with custom 'class', 'id', and 'content_class'."""
        self._run_align_block_test("align_custom_classes_and_id")

    def test_align_block_combination_params(self):
        """Test AlignBlock with a combination of parameters."""
        self._run_align_block_test("align_combination_params")

    def test_align_block_invalid_pos_value_falls_back_to_default(self):
        """Test AlignBlock with an invalid 'pos' value (should use default)."""
        # You might also want to check logger output if critical
        self._run_align_block_test("align_invalid_pos_value")

    def test_align_block_invalid_content_align_value_falls_back_to_default(self):
        """Test AlignBlock with an invalid 'content_align' value (should use default)."""
        self._run_align_block_test("align_invalid_content_align_value")

    def test_align_block_empty_content(self):
        """Test AlignBlock with empty content between tags."""
        self._run_align_block_test("align_empty_content")

    def test_align_block_content_with_markdown(self):
        """Test AlignBlock with markdown content inside."""
        self._run_align_block_test("align_content_with_markdown")

class TestProcessDimensionValue(unittest.TestCase):
    """
    Unit tests for the _process_dimension_value method of the AlignBlock.
    """

    def setUp(self):
        """Set up for each test method."""
        # Instantiate AlignBlock to test its method.
        # If AlignBlock requires specific Django settings or setup beyond simple
        # instantiation, this might need to be a Django TestCase or have settings configured.
        # For a helper method like this, ideally, it's testable with a simple instance.
        self.block = AlignBlock(reporter=MarkdownReporter(stdout=StringIO()))
        self.default_width = AlignBlock.DEFAULT_WIDTH  # "100%"
        self.default_height = AlignBlock.DEFAULT_HEIGHT # "auto"

    def test_process_auto_value(self):
        """Test that 'auto' is returned as 'auto'."""
        self.assertEqual(self.block._process_dimension_value("auto", self.default_height), "auto")
        self.assertEqual(self.block._process_dimension_value("AUTO", self.default_height), "auto")

    def test_process_explicit_percentage_values(self):
        """Test values with explicit '%' unit."""
        self.assertEqual(self.block._process_dimension_value("50%", self.default_width), "50%")
        self.assertEqual(self.block._process_dimension_value("100%", self.default_width), "100%")
        self.assertEqual(self.block._process_dimension_value("75.5%", self.default_width), "75.5%")
        self.assertEqual(self.block._process_dimension_value("0%", self.default_width), "0%")
        self.assertEqual(self.block._process_dimension_value("-50%", self.default_width), "-50%") # Regex allows this

    def test_process_explicit_px_values(self):
        """Test values with explicit 'px' unit."""
        self.assertEqual(self.block._process_dimension_value("150px", self.default_width), "150px")
        self.assertEqual(self.block._process_dimension_value("0px", self.default_width), "0px")
        self.assertEqual(self.block._process_dimension_value("120.7px", self.default_width), "120.7px")
        self.assertEqual(self.block._process_dimension_value("-100px", self.default_width), "-100px") # Regex allows this

    def test_process_unitless_number_le_100_becomes_percentage(self):
        """Test unitless numbers <= 100 become '%'."""
        self.assertEqual(self.block._process_dimension_value("50", self.default_width), "50%")
        self.assertEqual(self.block._process_dimension_value("100", self.default_width), "100%")
        self.assertEqual(self.block._process_dimension_value("0", self.default_width), "0%")
        self.assertEqual(self.block._process_dimension_value("75.5", self.default_width), "75.5%")
        self.assertEqual(self.block._process_dimension_value("50.0", self.default_width), "50%") # Handled by int() if is_integer()

    def test_process_unitless_number_gt_100_becomes_px(self):
        """Test unitless numbers > 100 become 'px'."""
        self.assertEqual(self.block._process_dimension_value("150", self.default_width), "150px")
        self.assertEqual(self.block._process_dimension_value("100.1", self.default_width), "100.1px")
        self.assertEqual(self.block._process_dimension_value("120.5", self.default_width), "120.5px")
        self.assertEqual(self.block._process_dimension_value("150.0", self.default_width), "150px") # Handled by int()

    def test_process_negative_unitless_number(self):
        """Test negative unitless numbers (current logic defaults or returns '0%')."""
        # Current _process_dimension_value logic for negative unitless numbers:
        # if num < 0: return "0%" (or default_value_with_unit based on implementation choice)
        # Assuming it's "0%" for this test as per one version of the suggested logic.
        self.assertEqual(self.block._process_dimension_value("-50", self.default_width), "0%")
        self.assertEqual(self.block._process_dimension_value("-100.5", self.default_width), "0%")


    def test_process_invalid_string_values_fallback_to_default(self):
        """Test invalid string values fall back to the provided default."""
        self.assertEqual(self.block._process_dimension_value("foo", self.default_width), self.default_width)
        self.assertEqual(self.block._process_dimension_value("50em", self.default_width), self.default_width) # 'em' not explicitly handled
        self.assertEqual(self.block._process_dimension_value("100 percent", self.default_width), self.default_width)
        self.assertEqual(self.block._process_dimension_value("px100", self.default_width), self.default_width)

    def test_process_invalid_values_with_units_fallback_to_default(self):
        """Test invalid numeric parts with units fall back to default."""
        self.assertEqual(self.block._process_dimension_value("abc%", self.default_width), self.default_width)
        self.assertEqual(self.block._process_dimension_value("xyzpx", self.default_width), self.default_width)
        self.assertEqual(self.block._process_dimension_value("--50%", self.default_width), self.default_width)


    def test_process_none_value_falls_back_to_default(self):
        """Test None input falls back to default."""
        # The str() conversion in _process_dimension_value will turn None into "None"
        # which will then fail parsing and fall back to default.
        self.assertEqual(self.block._process_dimension_value(None, self.default_width), self.default_width)

    def test_process_empty_string_falls_back_to_default(self):
        """Test empty string input falls back to default."""
        self.assertEqual(self.block._process_dimension_value("", self.default_width), self.default_width)

    def test_process_whitespace_around_valid_value(self):
        """Test values with surrounding whitespace."""
        # The regex re.fullmatch might be strict with whitespace unless explicitly handled.
        # Current regex: r"(-?\d*\.?\d+)\s*(px|%)" - allows space before unit.
        # If value_str is " 50% ", it depends if string is stripped before regex.
        # Assuming value_str is passed as is:
        self.assertEqual(self.block._process_dimension_value(" 75% ", self.default_width), self.default_width) # Will fail fullmatch
        self.assertEqual(self.block._process_dimension_value("75 %", self.default_width), "75%") # Space before unit is ok
        self.assertEqual(self.block._process_dimension_value(" 200 ", self.default_width), "200px") # Unitless number
        self.assertEqual(self.block._process_dimension_value("  auto  ", self.default_height), "auto") # str.lower() == "auto"

    def test_process_default_height_auto(self):
        """Test processing using default_height ('auto')."""
        self.assertEqual(self.block._process_dimension_value("50", self.default_height), "50%")
        self.assertEqual(self.block._process_dimension_value("invalid", self.default_height), "auto")


if __name__ == '__main__':
    unittest.main()