import unittest
import logging
from pathlib import Path
import re # Keep for potential future normalization, even if not used initially
from io import StringIO
import django_spellbook # For path to templates if needed
import os

# Django imports
from django.conf import settings
from django.test import TestCase
import django

# Your application imports
from django_spellbook.markdown.engine import SpellbookMarkdownEngine
from django_spellbook.blocks import SpellBlockRegistry
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter # Adjust if path changed
from django_spellbook.spellblocks import HeroSpellBlock # Ensure this path is correct

# --- Constants for File Paths ---
BASE_TEST_DIR = Path(__file__).parent
HERO_INPUT_MD_DIR = BASE_TEST_DIR / 'markdown_testers' / 'hero'
HERO_OUTPUT_HTML_DIR = BASE_TEST_DIR / 'html_testers' / 'hero' # Test-generated output
HERO_GOLDEN_HTML_DIR = BASE_TEST_DIR / 'html_goldens' / 'hero' # Expected correct output

# logging.disable(logging.CRITICAL) # Optional: Keep disabled for cleaner output

class TestHeroBlockIntegration(TestCase):
    """
    Integration tests for the HeroSpellBlock using the SpellbookMarkdownEngine.
    Focuses on rendering various configurations of the hero block
    and comparing against golden HTML files.
    """
    engine = None
    reporter_buffer = None
    reporter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_templates_dir = BASE_TEST_DIR / "templates" # For any test-specific templates

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
                        # Ensure hero.html and its partials can be found
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

        # Prepare directories for hero tests
        os.makedirs(HERO_OUTPUT_HTML_DIR, exist_ok=True)
        os.makedirs(HERO_GOLDEN_HTML_DIR, exist_ok=True)

    def _clear_and_register_hero_block(self):
        """Clears the registry and registers only the HeroSpellBlock."""
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
        else:
            # Fallback or warning if clearing mechanism is different
            print("Warning: Could not directly clear SpellBlockRegistry._registry")
            # SpellBlockRegistry.blocks = {} # If 'blocks' is the dict

        if hasattr(HeroSpellBlock, 'name') and HeroSpellBlock.name:
            SpellBlockRegistry._registry[HeroSpellBlock.name] = HeroSpellBlock
        else:
            raise ValueError("HeroSpellBlock must have a 'name' attribute for registration.")

    def setUp(self):
        """Set up for each test method."""
        self._clear_and_register_hero_block() # Use the hero-specific version

        self.reporter_buffer = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_buffer, report_level='debug')
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)

    def _normalize_html(self, html_content):
        """
        Placeholder for any HTML normalization needed for the hero block.
        For now, it just strips whitespace. Adapt if dynamic IDs or attributes appear.
        """
        # Example: If hero partials created dynamic ARIA labels or other IDs:
        # html_content = re.sub(r'aria-labelledby="dynamic-hero-title-\w+"', 'aria-labelledby="dynamic-hero-title-NORMALIZED"', html_content)
        return html_content.strip()

    def _run_hero_markdown_test(self, md_filename, golden_html_filename):
        """Helper method for hero block: read MD, render, and compare against golden HTML."""
        input_md_path = HERO_INPUT_MD_DIR / md_filename
        golden_html_path = HERO_GOLDEN_HTML_DIR / golden_html_filename
        output_html_path = HERO_OUTPUT_HTML_DIR / f"output_{md_filename.replace('.md', '.html')}"

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
                      f"Verify its content and re-run.")

        with open(golden_html_path, 'r', encoding='utf-8') as f:
            expected_html_raw = f.read()

        normalized_actual_html = self._normalize_html(actual_html)
        normalized_expected_html = self._normalize_html(expected_html_raw)

        self.assertMultiLineEqual(
            normalized_actual_html,
            normalized_expected_html,
            f"Normalized HTML for {md_filename} does not match golden file {golden_html_filename}.\n"
            f"Actual raw output in: {output_html_path}\n"
            f"Reporter output:\n{self.reporter_buffer.getvalue()}"
        )

    # --- Test Methods for HeroSpellBlock ---

    def test_hero_default_layout(self):
        """Test HeroSpellBlock with default layout and minimal content."""
        md_filename = "hero_default_layout.md"        
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_text_center_image_background(self):
        """Test text_center_image_background layout."""
        md_filename = "hero_text_center_image_bg.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_text_only_centered(self):
        """Test text_only_centered layout."""
        md_filename = "hero_text_only_centered.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_text_right_image_left(self):
        """Test text_right_image_left layout."""
        md_filename = "hero_text_right_image_left.md"        
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_image_top_text_bottom(self):
        """Test image_top_text_bottom layout."""
        md_filename = "hero_image_top_text_bottom.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_image_only_full(self):
        """Test image_only_full layout (no text content from inner block)."""
        md_filename = "hero_image_only_full.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_with_custom_class_and_styling(self):
        """Test hero with custom class, bg_color, text_color, text_bg_color."""
        md_filename = "hero_custom_styling.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))

    def test_hero_missing_image_alt_warning(self):
        """Test that a warning is logged if image_src is present but image_alt is missing."""
        md_filename = "hero_missing_image_alt_warning.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))
            
    def test_invalid_layout(self):
        """Test that an error is logged if an invalid layout is specified."""
        md_filename = "hero_invalid_layout.md"
        self._run_hero_markdown_test(md_filename, md_filename.replace(".md", ".html"))
