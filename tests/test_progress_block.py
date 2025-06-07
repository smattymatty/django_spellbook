import unittest
import logging
from pathlib import Path
import re
from io import StringIO
import django_spellbook
import os # For path handling

# Django imports
from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase # Using Django's TestCase for better integration
import django

# Your application imports
from django_spellbook.markdown.engine import SpellbookMarkdownEngine
from django_spellbook.blocks import SpellBlockRegistry # Assuming SpellBlockRegistry is the correct name
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter # Adjust if path changed
# Import the block to be tested
from django_spellbook.spellblocks import ProgressBarBlock # Ensure this path is correct

# Disable most logging for cleaner test output, can be adjusted
# logging.disable(logging.CRITICAL) # Keep disabled or set to logging.ERROR for less noise

# --- Constants for File Paths ---
# Assumes your tests are in a 'tests' directory at the root of your app or project
BASE_TEST_DIR = Path(__file__).parent
INPUT_MD_DIR = BASE_TEST_DIR / 'markdown_testers' / 'progress'
OUTPUT_HTML_DIR = BASE_TEST_DIR / 'html_testers' / 'progress' # Test-generated output
GOLDEN_HTML_DIR = BASE_TEST_DIR / 'html_goldens' / 'progress' # Expected correct output

class TestProgressBarBlockIntegration(TestCase): # Inherit from Django's TestCase
    """
    Integration tests for the ProgressBarBlock using the SpellbookMarkdownEngine.
    Focuses on rendering various configurations of the progress bar
    and comparing against golden HTML files.
    """
    engine = None
    reporter_buffer = None
    reporter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass() # Important for Django's TestCase

        cls.test_templates_dir = BASE_TEST_DIR / "templates" # For any test-specific templates

        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django_spellbook', # Your app
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                    # Add other necessary apps
                ],
                TEMPLATES=[
                    {
                        'BACKEND': 'django.template.backends.django.DjangoTemplates',
                        'DIRS': [str(cls.test_templates_dir), str(Path(django_spellbook.__file__).parent / 'templates')], # Add your app's templates too
                        'APP_DIRS': True, # Consider setting to False if DIRS is comprehensive
                        'OPTIONS': {
                            'debug': True, # Set to False for production-like testing if needed
                            'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                            ],
                            'builtins': [ # Ensure your spellbook_tags are loaded if used by the block's template
                                'django_spellbook.templatetags.spellbook_tags',
                            ]
                        },
                    }
                ],
                DATABASES={ # Minimal DB setup
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                },
                # Add any other settings your ProgressBarBlock or its template might depend on
            )
            django.setup()

        # Prepare directories
        os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
        os.makedirs(GOLDEN_HTML_DIR, exist_ok=True) # Ensure golden dir exists for reference

        # Initialize reporter and engine once for the class if state doesn't interfere
        # However, for SpellBlockRegistry, it's safer to handle it in setUp/tearDown
        # or ensure tests don't mutate the shared registry state in a conflicting way.

    def _clear_and_register_blocks(self):
        """Clears and re-registers specific blocks for test isolation."""
        # Clear the registry
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        else:
            # Fallback or warning if clearing mechanism is different
            print("Warning: Could not directly clear SpellBlockRegistry._registry")
            # Attempt to reinitialize or use a known method if available
            # SpellBlockRegistry.blocks = {} # If 'blocks' is the dict

        # Register only the ProgressBarBlock for this test suite
        # Assumes ProgressBarBlock.name is defined
        if ProgressBarBlock.name:
            # Or directly manipulate if necessary and understood:
            SpellBlockRegistry._registry[ProgressBarBlock.name] = ProgressBarBlock
        else:
            raise ValueError("ProgressBarBlock must have a 'name' attribute.")


    def setUp(self):
        """Set up for each test method."""
        self._clear_and_register_blocks()

        self.reporter_buffer = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_buffer, report_level='debug') # Or 'info'
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)
        # Ensure templates used by ProgressBarBlock can be found
        # This might involve checking settings.TEMPLATES['DIRS']


    def _normalize_html_ids(self, html_content):
        """
        Normalizes dynamically generated ID suffixes in the HTML content.
        Replaces 'progress-container-TIMESTAMP' with 'progress-container-NORMALIZED_ID'
        and 'popover-content-TIMESTAMP' with 'popover-content-NORMALIZED_ID'.
        """
        # Regex to find 'progress-container-' followed by a timestamp (digits)
        html_content = re.sub(r'id="progress-container-\d+"', 'id="progress-container-NORMALIZED_ID"', html_content)
        # Regex to find 'popover-content-' followed by a timestamp (digits)
        # This also handles cases where the suffix might have been derived from a non-timestamp unique_id in other tests
        html_content = re.sub(r'id="popover-content-[\w\d_]+"', 'id="popover-content-NORMALIZED_ID"', html_content)
        return html_content

    def _run_markdown_test(self, md_filename, golden_html_filename):
        """Helper method to read MD, render, and compare against golden HTML."""
        input_md_path = INPUT_MD_DIR / md_filename
        golden_html_path = GOLDEN_HTML_DIR / golden_html_filename
        output_html_path = OUTPUT_HTML_DIR / f"output_{md_filename.replace('.md', '.html')}"

        self.assertTrue(input_md_path.exists(), f"Markdown input file not found: {input_md_path}")

        with open(input_md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        actual_html = self.engine.parse_and_render(markdown_text)

        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(actual_html) # Save the raw actual output for debugging

        if not golden_html_path.exists():
            # Create the golden file with normalized IDs if it doesn't exist
            os.makedirs(golden_html_path.parent, exist_ok=True)
            normalized_for_golden_creation = self._normalize_html_ids(actual_html)
            with open(golden_html_path, 'w', encoding='utf-8') as f:
                f.write(normalized_for_golden_creation)
            print(f"INFO: Golden file CREATED with normalized IDs: {golden_html_path}")
            self.fail(f"Golden HTML file was missing, CREATED with normalized IDs: {golden_html_path}. "
                    f"Verify its content (especially the 'NORMALIZED_ID' parts) and re-run.")

        with open(golden_html_path, 'r', encoding='utf-8') as f:
            expected_html_raw = f.read()

        # Normalize both actual and expected HTML before comparison
        normalized_actual_html = self._normalize_html_ids(actual_html).strip()
        normalized_expected_html = self._normalize_html_ids(expected_html_raw).strip() # Also normalize the golden file content read

        self.assertMultiLineEqual(
            normalized_actual_html,
            normalized_expected_html,
            f"Normalized HTML for {md_filename} does not match golden file {golden_html_filename}.\n"
            f"Actual raw output in: {output_html_path}\n"
            f"Reporter output:\n{self.reporter_buffer.getvalue()}"
        )

    # --- Test Methods ---

    def test_progress_bar_default_values(self):
        """Test ProgressBarBlock with default parameters."""
        markdown_text = "{~ progress ~} \nDefault content\n {~~}" # Using your block syntax
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('<p><div\nclass="sb-progress-container sb-shadow-md sb-w-full', actual_html)
        self.assertIn('style="width: 0.0%;"', actual_html) # Assuming default value is 50 if not provided
        self.assertIn('sb-bg-primary', actual_html) # Assuming default color
        self.assertIn('<div class="sb-progress-popover-content', actual_html)
        self.assertIn('Default content', actual_html)
        self._run_markdown_test("progress_defaults.md", "progress_defaults.html")

    def test_progress_bar_with_value_and_label(self):
        """Test ProgressBarBlock with specified value and label."""
        markdown_text = '{~ progress value="75" label="Task A: {{percentage}}%"  ~}\nDetails for Task A\n{~~}'
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('style="width: 75.0%;"', actual_html)
        self.assertIn('Task A: 75.0%', actual_html)
        self.assertIn('Details for Task A', actual_html)
        self._run_markdown_test("progress_value_label.md", "progress_value_label.html")

    def test_progress_bar_custom_colors_and_height(self):
        """Test custom colors, background, and height."""
        markdown_text = ('{~ progress value="30" color="success" bg_color="neutral-25" height="lg" '
                         'content_bg_color="success-75" content_color="white" ~}\nSuccess details\n{~~}')
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('sb-bg-success', actual_html) # Bar fill
        self.assertIn('sb-bg-neutral-25', actual_html) # Bar track
        self.assertIn('sb-h-16', actual_html) # Assuming lg maps to sb-h-16
        # Check popover styling (this depends on how your template applies these)
        # This might be inline styles or classes like sb-bg-success-75 sb-text-white
        self.assertIn('sb-bg-success-75', actual_html) # Popover background
        self.assertIn('sb-white', actual_html) # Popover text color
        self.assertIn('Success details', actual_html)
        self._run_markdown_test("progress_custom_appearance.md", "progress_custom_appearance.html")

    def test_progress_bar_striped_animated_no_rounding(self):
        """Test striped, animated, and non-rounded progress bar."""
        markdown_text = ('{~ progress value="60" color="info" striped="true" animated="true" '
                         'rounded="false" label="Processing..." ~}\nProcessing data...\n{~~}')
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('sb-progress-bar-striped', actual_html) # Ensure BEM modifier if that's your convention
        self.assertIn('sb-progress-bar-animated', actual_html)
        self.assertNotIn('sb-border-radius-md', actual_html) # If rounded="false" removes this class
        self.assertIn('Processing...', actual_html)
        self._run_markdown_test("progress_striped_animated.md", "progress_striped_animated.html")

    def test_progress_bar_max_value_interpolation(self):
        """Test with max_value and label interpolation."""
        markdown_text = ('{~ progress value="250" max_value="500" '
                         'label="Chapter {{value}} of {{max_value}} ({{percentage}}%)" ~}\nChapter progress\n{~~}')
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('style="width: 50.0%;"', actual_html)
        self.assertIn('aria-valuenow="50.0"', actual_html) # Check raw value if used
        self.assertIn('Chapter 250.0 of 500.0 (50.0%)', actual_html)
        self.assertIn('Chapter progress', actual_html)
        self._run_markdown_test("progress_max_value.md", "progress_max_value.html")

    def test_progress_bar_no_popover_content(self):
        """Test progress bar rendering when no content is provided for the popover."""
        markdown_text = '{~ progress value="90" label="Almost there!" ~}{~~}' # Note the space for empty content
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('Almost there!', actual_html)
        # Check that the popover div is present but empty, or handled as per your template logic
        # (e.g., the div might not be rendered at all if content is empty)
        popover_div_regex = r'<div class="sb-progress-popover-content.*?style="display: none;">(.*?)</div>'
        match = re.search(popover_div_regex, actual_html, re.DOTALL)
        self.assertFalse(match, "Popover div found.")
        self.assertIn('aria-valuenow="90.0"', actual_html) # Check raw value if used
        # Assuming empty content means just whitespace or nothing between <p> tags if your markdown parser adds them
        self._run_markdown_test("progress_no_popover_content.md", "progress_no_popover_content.html")

    def test_progress_bar_with_id_and_custom_class(self):
        """Test with custom ID and class attributes."""
        markdown_text = ('{~ progress value="10" id="my-special-progress" class="extra-styles another-class" ~}'
                        '\nSpecial popover\n{~~}')
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('id="my-special-progress"', actual_html)
        self.assertIn('class="sb-progress-container sb-shadow-md sb-w-full extra-styles another-class"', actual_html)
        self.assertIn('id="popover-content-my-special-progress"', actual_html) # Assuming popover ID derives from container ID
        self.assertIn('Special popover', actual_html)
        self._run_markdown_test("progress_id_class.md", "progress_id_class.html")
        
    def test_international_content(self):
        """Test with multiple languages and content."""
        markdown_text = ('{~ progress value="50" label="التقدم: {{percentage}}%" color="secondary" content_bg_color="neutral-10" content_color="black" ~}'
                         'محتوى دولي: مرحبًا بالعالم! こんにちは世界！ 안녕하세요 세계! {نواتج التعلم}'
                         '{~~}')
        actual_html = self.engine.parse_and_render(markdown_text)
        self.assertIn('التقدم: 50.0%', actual_html)
        
        self._run_markdown_test("progress_international_content.md", "progress_international_content.html")

# Allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()
    
    
import unittest
import logging
from pathlib import Path
from io import StringIO
import os
from unittest import mock # Crucial for capturing log messages

# Django imports
from django.conf import settings
from django.test import TestCase # Using Django's TestCase
import django

# Your application imports
from django_spellbook.markdown.engine import SpellbookMarkdownEngine
from django_spellbook.blocks import SpellBlockRegistry
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter
from django_spellbook.spellblocks import ProgressBarBlock

# --- Constants (can be shared or redefined if paths differ) ---
BASE_TEST_DIR = Path(__file__).parent
# No specific markdown files needed for these tests if we pass markdown text directly
# but you might want golden files if the *rendered output with defaults* is important
OUTPUT_HTML_DIR_ERRORS = BASE_TEST_DIR / 'html_testers' / 'progress_errors'
GOLDEN_HTML_DIR_ERRORS = BASE_TEST_DIR / 'html_goldens' / 'progress_errors'


class TestProgressBarBlockErrorHandling(TestCase):
    """
    Tests for error handling and default value assignment in ProgressBarBlock,
    specifically focusing on logging invalid 'value' and 'max_value' parameters.
    """
    engine = None
    reporter_buffer = None # For SpellbookMarkdownEngine's reporter
    reporter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_templates_dir = BASE_TEST_DIR / "templates"

        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=['django_spellbook', 'django.contrib.auth', 'django.contrib.contenttypes'],
                TEMPLATES=[{
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [str(cls.test_templates_dir), str(Path(django_spellbook.__file__).parent / 'templates')],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'debug': True,
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ],
                        'builtins': ['django_spellbook.templatetags.spellbook_tags']
                    },
                }],
                DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
                LOGGING = { # Configure logging to capture warnings
                    'version': 1,
                    'disable_existing_loggers': False,
                    'handlers': {
                        'console': {
                            'class': 'logging.StreamHandler',
                        },
                    },
                    'loggers': {
                        'django_spellbook.spellblocks': { # Target your block's logger
                            'handlers': ['console'],
                            'level': 'WARNING', # Capture WARNING and above
                            'propagate': True,
                        },
                    },
                }
            )
            django.setup()
        os.makedirs(OUTPUT_HTML_DIR_ERRORS, exist_ok=True)
        os.makedirs(GOLDEN_HTML_DIR_ERRORS, exist_ok=True)


    def _clear_and_register_blocks(self):
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        if ProgressBarBlock.name:
            SpellBlockRegistry._registry[ProgressBarBlock.name] = ProgressBarBlock
        else:
            raise ValueError("ProgressBarBlock must have a 'name' attribute.")

    def setUp(self):
        self._clear_and_register_blocks()
        self.reporter_buffer = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_buffer, report_level='debug')
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)
        # self.logger_patcher = mock.patch('django_spellbook.spellblocks.progress_bar_block.logger') # Patch the specific logger
        # self.mock_logger = self.logger_patcher.start()
        # self.addCleanup(self.logger_patcher.stop) # Ensure patch is stopped

    def _normalize_html_ids(self, html_content):
        html_content = re.sub(r'id="progress-container-([^"]+)"', r'id="progress-container-NORMALIZED_ID"', html_content)
        html_content = re.sub(r'id="popover-content-([^"]+)"', r'id="popover-content-NORMALIZED_ID"', html_content)
        return html_content

    def _run_error_case_test(self, md_text,
                             expected_value_in_html, expected_max_value_in_html="100.0",
                             golden_html_filename=None): # Parameter for logger name
        
        logger_name_to_assert = 'django_spellbook.spellblocks.progress_bar_block' # Default, assuming __name__ in block
        # If ProgressBarBlock explicitly defines its logger name, e.g., self.logger = logging.getLogger('ProgressBarBlockLogger')
        # then you'd use 'ProgressBarBlockLogger' or pass it in.
        # For now, let's assume it's the module's logger.

        # Initialize actual_html here so it's defined for the golden file logic even if assertLogs fails early
        actual_html = ""

        
        actual_html = self.engine.parse_and_render(md_text)


        self.assertIn(f'aria-valuenow="{expected_value_in_html}"', actual_html)
        self.assertIn(f'aria-valuemax="{expected_max_value_in_html}"', actual_html)


        if golden_html_filename:
            output_html_path = OUTPUT_HTML_DIR_ERRORS / f"output_{golden_html_filename}"
            golden_html_path = GOLDEN_HTML_DIR_ERRORS / golden_html_filename
            
            os.makedirs(output_html_path.parent, exist_ok=True) # Ensure output dir exists
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(actual_html)

            if not golden_html_path.exists():
                os.makedirs(golden_html_path.parent, exist_ok=True)
                normalized_for_golden = self._normalize_html_ids(actual_html)
                with open(golden_html_path, 'w', encoding='utf-8') as f:
                    f.write(normalized_for_golden)
                self.fail(f"Golden HTML file for error case CREATED: {golden_html_path}. Verify and re-run.")

            with open(golden_html_path, 'r', encoding='utf-8') as f:
                expected_html_raw = f.read()

            normalized_actual_html = self._normalize_html_ids(actual_html).strip()
            normalized_expected_html = self._normalize_html_ids(expected_html_raw).strip()

            self.assertMultiLineEqual(normalized_actual_html, normalized_expected_html,
                                      f"HTML for {golden_html_filename} mismatch. Check {output_html_path}")

    # --- Test Methods for Error Handling ---

    def test_invalid_max_value_string(self):
        markdown_text = '{~ progress value="50" max_value="not-a-number" ~}Invalid Max~ {~~}'
        self._run_error_case_test(
            md_text=markdown_text,
            expected_value_in_html="50.0",
            expected_max_value_in_html="100",
            golden_html_filename="error_invalid_max_value_string.html" # ADD FILENAME
        )

    def test_invalid_max_value_zero(self):
        markdown_text = '{~ progress value="20" max_value="0" ~}Max Value Zero {~~}'
        self._run_error_case_test(
            md_text=markdown_text,
            expected_value_in_html="20.0",
            expected_max_value_in_html="100",
            golden_html_filename="error_invalid_max_value_zero.html" # ADD FILENAME
        )

    def test_invalid_max_value_negative(self):
        markdown_text = '{~ progress value="30" max_value="-10" ~}Max Value Negative~ {~~}'
        self._run_error_case_test(
            md_text=markdown_text,
            expected_value_in_html="30.0",
            expected_max_value_in_html="100",
            golden_html_filename="error_invalid_max_value_negative.html" # ADD FILENAME
        )

    def test_invalid_value_string(self):
        markdown_text = '{~ progress value="not-a-number" max_value="200" ~}Invalid Value {~~}'
        self._run_error_case_test(
            md_text=markdown_text,
            expected_value_in_html="0.0",
            expected_max_value_in_html="100",
            golden_html_filename="error_invalid_value_string.html" # ADD FILENAME
        )

    def test_value_greater_than_max_value_renders_correctly(self):
        markdown_text = '{~ progress value="150" max_value="100" label="{{percentage}}" ~}Value Exceeds Max Popover{~~}' # Added popover content
        # No specific log message part is expected for this behavior from your snippets
        # The assertions for aria-valuenow should use the raw value.
        # The visual percentage (style width, label) should be capped.
        self._run_error_case_test(
            md_text=markdown_text,
            expected_value_in_html="100.0", # aria-valuenow should be the raw value
            expected_max_value_in_html="100",
            golden_html_filename="progress_value_greater_than_max_value.html",
        )
if __name__ == '__main__':
    unittest.main()