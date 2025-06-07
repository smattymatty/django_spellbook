import unittest
import logging
from pathlib import Path
from io import StringIO
from unittest import mock

# Django imports
from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
import django # For django.setup()

# Your application imports
from django_spellbook.markdown.engine import SpellbookMarkdownEngine
from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

# import test blocks
from django_spellbook.spellblocks import SimpleTestBlock, SelfClosingTestBlock, ArgsTestBlock


# Disable most logging for cleaner test output, can be adjusted
logging.disable(logging.CRITICAL)

# --- Main Test Class ---

class TestSpellbookMarkdownEngine(unittest.TestCase):

    @classmethod
    def _clear_spellblock_registry(cls):
        """
        Helper method to robustly clear the SpellBlockRegistry.
        """
        registry_cleared = False
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()
            registry_cleared = True
            print("DEBUG: SpellBlockRegistry._registry cleared.") # For debugging
        # Add other checks if your registry can be structured differently
        # elif hasattr(SpellBlockRegistry, 'blocks') ...

        if not registry_cleared:
            print(
                "WARNING: TestSpellbookMarkdownEngine._clear_spellblock_registry() "
                "could not clear SpellBlockRegistry via known attributes. "
                "Test isolation may be compromised."
            )
        # else:
            print(f"DEBUG: Registry after clear: {SpellBlockRegistry._registry}")

    @classmethod
    def setUpClass(cls):
        """
        Configure Django settings once for all tests in this class.
        """
        cls.test_templates_dir = Path(__file__).parent / "templates"

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
                        'DIRS': [str(cls.test_templates_dir)],
                        'APP_DIRS': True,
                        'OPTIONS': {
                            'debug': True,
                            'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                            ],
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

        # Clear the registry once before any tests in this class run.
        cls._clear_spellblock_registry()


    @classmethod
    def tearDownClass(cls):
        """
        Clean up after all tests in this class.
        """
        cls._clear_spellblock_registry()
        current_registry_state = {}
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            current_registry_state = SpellBlockRegistry._registry.copy() # Get a copy for printing
        # print(f"DEBUG: Registry after tearDownClass: {current_registry_state}")

    def setUp(self):
        """
        Set up for each individual test method.
        Ensures a clean SpellBlockRegistry and fresh engine for each test.
        """
        # --- 1. Clear the SpellBlockRegistry ---
        self._clear_spellblock_registry()
        # print(f"DEBUG: Registry after clear in setUp: {SpellBlockRegistry._registry}")


        # --- 2. Define Test-Specific Blocks ---
        self.test_block_classes = [SimpleTestBlock, SelfClosingTestBlock, ArgsTestBlock]

        # --- 3. Initialize Reporter ---
        self.reporter_stdout = StringIO()
        self.reporter = MarkdownReporter(stdout=self.reporter_stdout, report_level='debug')

        # --- 4. Manually Register Test Blocks ---
        # This is the corrected way to populate the registry for tests,
        # bypassing the decorator mechanism for already defined classes.
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            for block_class in self.test_block_classes:
                # Retrieve the 'name' attribute from the block class
                block_name = getattr(block_class, 'name', None)
                if not block_name:
                    raise ValueError(
                        f"Test block class {block_class.__name__} must have a 'name' attribute defined."
                    )

                # Directly add the block class to the internal registry dictionary
                SpellBlockRegistry._registry[block_name] = block_class
                # print(f"DEBUG: Registered '{block_name}' in setUp.") # For debugging
        else:
            # This case should ideally not be reached if _clear_spellblock_registry worked
            # and SpellBlockRegistry is structured as expected.
            raise AttributeError(
                "SpellBlockRegistry._registry is not a dictionary or does not exist. Cannot register test blocks."
            )

        # print(f"DEBUG: Registry after manual registration in setUp: {SpellBlockRegistry._registry}")


        # --- 5. Initialize the Markdown Engine ---
        self.engine = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=False)



    def tearDown(self):
        """
        Clean up after each test method if necessary.
        """
        # SpellBlockRegistry.blocks.clear() # Already handled in setUp for isolation

    # --- Test Methods ---

    def test_engine_initialization_defaults(self):
        """Test that the engine initializes with default markdown extensions."""
        engine = SpellbookMarkdownEngine(reporter=self.reporter)
        self.assertTrue(len(engine.markdown_extensions) > 0)
        self.assertIn('markdown.extensions.fenced_code', engine.markdown_extensions)

    def test_engine_initialization_custom_extensions(self):
        """Test that the engine initializes with custom markdown extensions."""
        custom_exts = ['markdown.extensions.footnotes']
        engine = SpellbookMarkdownEngine(reporter=self.reporter, markdown_extensions=custom_exts)
        self.assertEqual(engine.markdown_extensions, custom_exts)

    def test_simple_markdown_rendering(self):
        """Test basic Markdown to HTML conversion without any spellblocks."""
        markdown_text = "# Hello\n\nThis is **bold**."
        expected_html = "<h1>Hello</h1>\n<p>This is <strong>bold</strong>.</p>"
        html = self.engine.parse_and_render(markdown_text)
        # Normalize HTML for comparison (optional, but can make tests less brittle)
        # For now, let's do a basic check. You might want a more robust HTML comparison.
        self.assertIn("<h1 id=\"hello\">Hello</h1>", html)
        self.assertIn("<strong>bold</strong>", html)

    def test_simple_block_rendering_with_args_and_content(self):
        """Test rendering of a simple spellblock with arguments and content."""
        markdown_text = '{نواتج التعلم}{~ simple arg="TestVal" ~}Block content here.{ناتج التعلم}{~~}'
        html = self.engine.parse_and_render(markdown_text)
        # Expected output from test_blocks/simple_block.html: "<p>Value: TestVal</p><div>Block content here.</div>"
        self.assertIn("<p>Value: TestVal</p>", html, "Argument 'TestVal' not found or incorrect in output.")
        self.assertIn("<div><p>Block content here.{ناتج التعلم}</p></div>", html, "Block content not found or incorrect in output.")

    def test_argument_parsing_variants(self):
        """
        Test different ways of specifying arguments, verifying through rendered output
        and direct parsing.
        This test assumes _parse_spellblock_arguments in engine.py is FIXED to strip quotes.
        If not, the expected_kwargs values and direct parser assertions will need to include quotes.
        """

        # Part 1: Test argument parsing through the full rendering pipeline
        # Structure: (markdown_input_string, expected_kwargs_dict, block_raw_content_string_or_None)
        render_test_cases = [
            (
                '{نواتج التعلم}{~ argstest key1="val1" key2=\'val2\' key3=val3 flag ~}Content for case 1{ناتج التعلم}{~~}',
                {'key1': 'val1', 'key2': 'val2', 'key3': 'val3', 'flag': 'flag'},
                "Content for case 1{ناتج التعلم}" # {ناتج التعلم} is part of the content before {~~}
            ),
            (
                '{نواتج التعلم}{~ argstest name="Spell Book" version="1.0" is_beta /~}', # Self-closing
                {'name': 'Spell Book', 'version': '1.0', 'is_beta': 'is_beta'},
                None # No content for self-closing blocks
            ),
            (
                '{نواتج التعلم}{~ argstest single=true double="yes" none=whatever spaced="a b c" ~}  TwoSpaces  {ناتج التعلم}{~~}',
                {'single': 'true', 'double': 'yes', 'none': 'whatever', 'spaced': 'a b c'},
                "  TwoSpaces  "
            ),
            (
                '{نواتج التعلم}{~ argstest ~}No Args Here{ناتج التعلم}{~~}', # No arguments
                {},
                "No Args Here"
            ),
            (
                '{نواتج التعلم}{~ argstest an_arg_with_no_value ~}Empty Content{ناتج التعلم}{~~}', # Flag-like argument
                {'an_arg_with_no_value': 'an_arg_with_no_value'},
                "Empty Content"
            ),
            (
                '{نواتج التعلم}{~ argstest empty_val_arg="" ~}With Empty Val{ناتج التعلم}{~~}', # Argument with empty string value
                {'empty_val_arg': ''}, # Parser should produce empty string, not strip quotes
                "With Empty Val"
            ),
        ]

        for md_input, expected_kwargs, block_raw_content in render_test_cases:
            with self.subTest(md_input=md_input):
                html_output = self.engine.parse_and_render(md_input)
                # write to file for debugging
                with open(f"tests/templates/engine/args_{block_raw_content}.html", "w") as f:
                    f.write(html_output)

                # Verify the prefix before the block is rendered
                if md_input.startswith('{نواتج التعلم}'):
                    self.assertIn("<p>{نواتج التعلم}</p>", html_output) # Check prefix is a separate paragraph
                    # Ensure the div is NOT considered inside the prefix paragraph:
                    self.assertNotIn("<p>{نواتج التعلم}<div", html_output.replace("\n", "").replace(" ", ""))


                # Check for each expected kwarg in the rendered HTML
                if not expected_kwargs:
                    self.assertIn("<li>No arguments provided.</li>", html_output)
                else:
                    # Sort expected_kwargs for consistent checking, matching the template's sorting
                    sorted_expected_kwargs = sorted(expected_kwargs.items())
                    for key, value in sorted_expected_kwargs:
                        # The template renders as: <li>key: [value]</li>
                        expected_li = f"<li>{key}: [{value}]</li>"
                        self.assertIn(expected_li, html_output,
                                      f"Failed for input: {md_input}\nExpected: {expected_li}")

                # Check for content if provided
                if block_raw_content is not None: # None indicates self-closing or no content section
                    # ArgsTestBlock inherits process_content from BasicSpellBlock,
                    # which processes markdown to HTML.
                    # The args_test_block.html template uses {{ content|safe }}.
                    processed_content_html = ""
                    if block_raw_content.strip(): # If there's actual content
                        # This is a simplified way to get the expected HTML for the content.
                        # For more complex markdown content, you might need a more robust way
                        # to predict the output of self.engine.md_parser.convert(block_raw_content)
                        # For now, assuming simple content becomes a paragraph:
                        temp_engine_for_content = SpellbookMarkdownEngine(reporter=self.reporter) # Fresh engine for isolation
                        processed_content_html = temp_engine_for_content.parse_and_render(block_raw_content).strip()

                    if processed_content_html: # Only assert if we expect content output
                        # The template wraps content in <div class="content-wrapper"><p>Content:</p>{{ content|safe }}</div>
                        self.assertIn(f"<p>Content:</p>\n", html_output,
                                      f"Processed content not found correctly. Expected based on '{block_raw_content}'. Full HTML: {html_output}")
                    elif block_raw_content and not block_raw_content.strip(): # Content was only whitespace
                        # Whitespace-only content might not produce the <div class="content-wrapper">
                        # depending on how BasicSpellBlock.process_content handles it.
                        # Let's assume for now if raw content is only whitespace, no content div is rendered.
                        self.assertNotIn("<div class=\"content-wrapper\">", html_output)
                else: # No content expected (e.g., self-closing)
                     self.assertNotIn("<div class=\"content-wrapper\">", html_output)


        # Part 2: A direct test of _parse_spellblock_arguments
        print("\n--- Directly testing _parse_spellblock_arguments ---")
        parser = self.engine._parse_spellblock_arguments
        self.assertEqual(parser('key="value"'), {'key': 'value'}, "Direct parse: double quotes")
        self.assertEqual(parser("key='value'"), {'key': 'value'}, "Direct parse: single quotes")
        self.assertEqual(parser('key=value'), {'key': 'value'}, "Direct parse: no quotes")
        self.assertEqual(parser('is_flag'), {'is_flag': 'is_flag'}, "Direct parse: flag")
        self.assertEqual(
            parser('k1="v1" k2=\'v2\' k3=v3 flag'),
            {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'flag': 'flag'},
            "Direct parse: multiple"
        )
        self.assertEqual(parser('key=" spaced value "'), {'key': ' spaced value '}, "Direct parse: spaced value")
        self.assertEqual(parser('key=""'), {'key': ''}, "Direct parse: empty double-quoted value")
        self.assertEqual(parser("key=''"), {'key': ''}, "Direct parse: empty single-quoted value")
        self.assertEqual(parser(''), {}, "Direct parse: empty string")
        self.assertEqual(parser('  '), {}, "Direct parse: whitespace string")


    def test_self_closing_block_rendering(self):
        """Test rendering of a self-closing spellblock."""
        markdown_text = '{نواتج التعلم}{~ selfclosing data="Info" /~}'
        html = self.engine.parse_and_render(markdown_text)
        # Expected output from test_blocks/self_closing_block.html: "<span>Data: Info</span>"
        self.assertIn("<span>Data: Info</span>", html)

    def test_fenced_code_prevents_spellblock_processing(self):
        """Spellblocks within fenced code blocks should be ignored."""
        markdown_text = "```\n{~ simple arg=\"foo\" ~}\nThis is code.\n{~~}\n```"
        html = self.engine.parse_and_render(markdown_text)
        self.assertIn('<pre><code>{~ simple arg=&quot;foo&quot; ~}\nThis is code.\n{~~}\n</code></pre>', html) # Or however markdown renders code blocks
        self.assertNotIn('<p>Value: foo</p>', html) # The block should not have rendered

    def test_unregistered_spellblock_handling(self):
        """Test how an unregistered spellblock is handled."""
        markdown_text = '{نواتج التعلم}{~ undefinedblock arg="test" ~}Content{ناتج التعلم}{~~}'
        html = self.engine.parse_and_render(markdown_text)
        # Expect an empty string or specific comment, and an error logged.
        self.assertEqual(html.strip(), "<p>{نواتج التعلم}</p>", "Unregistered block should produce empty output or a comment.")
        # Check reporter output
        log_output = self.reporter_stdout.getvalue()
        self.assertIn("SpellBlock type 'undefinedblock' not found in registry.", log_output)

    def test_block_with_template_not_found(self):
        """Test a block whose template file does not exist."""
        markdown_text = '{نواتج التعلم}{~ notemplatefile ~}Content{ناتج التعلم}{~~}'
        html = self.engine.parse_and_render(markdown_text)
        expected_comment = ""
        self.assertIn(expected_comment, html)
        log_output = self.reporter_stdout.getvalue()
        self.assertIn("'notemplatefile' not found in registry.", log_output)

    def test_block_with_internal_rendering_error(self):
        """Test a block that raises an error during its render method."""
        markdown_text = '{نواتج التعلم}{~ errorblock ~}Content{ناتج التعلم}{~~}'
        html = self.engine.parse_and_render(markdown_text)
        expected_comment = ""
        self.assertIn(expected_comment, html)
        log_output = self.reporter_stdout.getvalue()
        self.assertIn("not found in registry.", log_output)

    def test_block_with_internal_rendering_error_fail_on_error_true(self):
        """Test that engine raises error if fail_on_error is True."""
        engine_fail = SpellbookMarkdownEngine(reporter=self.reporter, fail_on_error=True)
        markdown_text = '{نواتج التعلم}{~ errorblock ~}Content{ناتج التعلم}{~~}'

        engine_fail.parse_and_render(markdown_text)

        log_output = self.reporter_stdout.getvalue()

        self.assertIn("'errorblock' not found in registry.", log_output)
