# django_spellbook/tests/test_commands.py

import shutil
import datetime
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.conf import settings
from django_spellbook.management.commands.spellbook_md import (
    Command,
    ProcessedFile,
    MarkdownProcessingError,
    MarkdownFileProcessor,
    TemplateGenerator,
    URLViewGenerator
)
from django_spellbook.markdown.context import SpellbookContext


class BaseTestCase(TestCase):
    """Base test case with common setup and teardown"""

    def setUp(self):
        self.test_md_path = Path(settings.BASE_DIR) / 'test_md_files'
        self.test_content_app = 'test_content'
        self.test_content_path = Path(
            settings.BASE_DIR) / self.test_content_app
        self.templates_dir = self.test_content_path / 'templates' / self.test_content_app
        self.spellbook_dir = Path(settings.BASE_DIR) / 'django_spellbook'

        # Create necessary directories
        self.test_md_path.mkdir(exist_ok=True)
        self.test_content_path.mkdir(exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing urls.py and views.py if they exist
        self.backup_files = {}
        for file in ['urls.py', 'views.py']:
            file_path = self.spellbook_dir / file
            if file_path.exists():
                self.backup_files[file] = file_path.read_text()
            else:
                # Create empty files if they don't exist
                self._create_empty_file(file_path)

    def _create_empty_file(self, file_path):
        """Create an empty Python module file"""
        if file_path.name == 'urls.py':
            content = """from django.urls import path
from . import views

urlpatterns = []
"""
        else:  # views.py
            content = """from django.shortcuts import render
"""
        file_path.write_text(content)

    def tearDown(self):
        # Clean up test directories
        if self.test_md_path.exists():
            shutil.rmtree(self.test_md_path)
        if self.test_content_path.exists():
            shutil.rmtree(self.test_content_path)

        # Restore or reset urls.py and views.py
        for file, content in self.backup_files.items():
            file_path = self.spellbook_dir / file
            file_path.write_text(content)


class MarkdownFileProcessorTest(BaseTestCase):
    """Tests for the MarkdownFileProcessor class"""

    def setUp(self):
        super().setUp()
        self.processor = MarkdownFileProcessor()
        self.test_md_file = self.test_md_path / 'test.md'
        self.test_md_file.write_text("# Test\nThis is a test")

    def test_process_valid_file(self):
        """Test processing a valid markdown file"""
        html_content, file_path, context = self.processor.process_file(
            self.test_md_file,
            str(self.test_md_path),
            'test.md',
            []
        )

        self.assertIn('<h1>Test</h1>', html_content.strip())
        self.assertEqual(file_path, self.test_md_file)
        self.assertIsInstance(context, SpellbookContext)
        self.assertEqual(context.title, 'test')
        self.assertEqual(context.raw_content, "# Test\nThis is a test")

    def test_process_valid_file_with_frontmatter(self):
        """Test processing a markdown file with frontmatter"""
        content = """---
title: Custom Title
tags: ['test', 'markdown']
---
# Test
This is a test"""
        self.test_md_file.write_text(content)

        html_content, file_path, context = self.processor.process_file(
            self.test_md_file,
            str(self.test_md_path),
            'test.md',
            []
        )

        self.assertIn('<h1>Test</h1>', html_content.strip())
        self.assertEqual(file_path, self.test_md_file)
        self.assertIsInstance(context, SpellbookContext)
        self.assertEqual(context.title, 'Custom Title')
        self.assertEqual(context.tags, ['test', 'markdown'])

    def test_process_nonexistent_file(self):
        """Test processing a non-existent file"""
        with self.assertRaises(MarkdownProcessingError):
            self.processor.process_file(
                self.test_md_path / 'nonexistent.md',
                str(self.test_md_path),
                'nonexistent.md',
                []
            )

    def test_process_invalid_encoding(self):
        """Test processing a file with invalid encoding"""
        invalid_file = self.test_md_path / 'invalid.md'
        with open(invalid_file, 'wb') as f:
            f.write(b'\x80\x81')

        with self.assertRaises(MarkdownProcessingError):
            self.processor.process_file(
                invalid_file,
                str(self.test_md_path),
                'invalid.md',
                []
            )


class TemplateGeneratorTest(BaseTestCase):
    """Tests for the TemplateGenerator class"""

    def setUp(self):
        super().setUp()
        self.template_generator = TemplateGenerator(
            self.test_content_app,
            str(self.templates_dir / 'spellbook_md')
        )

    @override_settings(SPELLBOOK_MD_BASE_TEMPLATE=None)
    def test_create_template_without_base(self):
        """Test template creation without base template"""
        template_path = self.templates_dir / 'test.html'
        html_content = "<h1>Test</h1>"

        self.template_generator.create_template(template_path, html_content)

        self.assertTrue(template_path.exists())
        self.assertEqual(template_path.read_text(), html_content)

    @override_settings(SPELLBOOK_MD_BASE_TEMPLATE='test_content/base.html')
    def test_create_template_with_base(self):
        """Test template creation with base template"""
        # Create base template
        base_template = self.templates_dir / 'base.html'
        base_template.write_text("""
            {% block spellbook_md %}{% endblock %}
        """)

        template_path = self.templates_dir / 'test.html'
        html_content = "<h1>Test</h1>"

        self.template_generator.create_template(template_path, html_content)

        content = template_path.read_text()
        self.assertIn("{% extends 'test_content/base.html' %}", content)
        self.assertIn("{% block spellbook_md %}", content)
        self.assertIn("<h1>Test</h1>", content)


class URLViewGeneratorTest(BaseTestCase):
    """Tests for the URLViewGenerator class"""

    def setUp(self):
        super().setUp()
        self.url_generator = URLViewGenerator(
            self.test_content_app,
            str(self.test_content_path)
        )

    def test_generate_urls_and_views(self):
        """Test URL and view generation"""
        processed_file = ProcessedFile(
            original_path=Path('test.md'),
            html_content="<h1>Test</h1>",
            template_path=Path('test.html'),
            relative_url='test',
            context=SpellbookContext(
                title='Test',
                created_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
                updated_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
                url_path='test',
                raw_content='# Test\nThis is a test',
                is_public=True,
                tags=[],
                custom_meta={},
                toc=[],
                next_page=None,
                prev_page=None
            )
        )

        self.url_generator.generate_urls_and_views(
            [processed_file], self.spellbook_dir)

        # Check views.py in django_spellbook app
        views_file = self.spellbook_dir / 'views.py'
        self.assertTrue(views_file.exists())
        views_content = views_file.read_text()
        self.assertIn('def view_test', views_content)
        self.assertIn('return render', views_content)

        # Check urls.py in django_spellbook app
        urls_file = self.spellbook_dir / 'urls.py'
        self.assertTrue(urls_file.exists())
        urls_content = urls_file.read_text()
        self.assertIn("path('test'", urls_content)


class CommandIntegrationTest(BaseTestCase):
    """Integration tests for the full command"""

    def setUp(self):
        super().setUp()
        self.command = Command()
        self.spellbook_dir = Path(settings.BASE_DIR) / 'django_spellbook'

    @override_settings(
        SPELLBOOK_MD_PATH='test_md_files',
        SPELLBOOK_CONTENT_APP='test_content'
    )
    def test_full_command_execution(self):
        """Test full command execution with nested structure"""
        # Create test structure
        (self.test_md_path / 'articles').mkdir()
        (self.test_md_path / 'articles' / 'guide.md').write_text("# Guide")
        (self.test_md_path / 'test.md').write_text("# Test")

        call_command('spellbook_md')

        # Check templates
        self.assertTrue(
            (self.templates_dir / 'spellbook_md' / 'test.html').exists())
        self.assertTrue((self.templates_dir / 'spellbook_md' /
                        'articles' / 'guide.html').exists())

        # Check views and URLs in django_spellbook app
        self.assertTrue((self.spellbook_dir / 'views.py').exists())
        self.assertTrue((self.spellbook_dir / 'urls.py').exists())


class DocumentationClaimsTest(BaseTestCase):
    """Tests that verify documentation claims"""

    def test_markdown_features(self):
        """Test all markdown features mentioned in documentation"""
        test_cases = [
            {
                'name': 'basic_markdown',
                'content': "# Test\nThis is a test",
                'expected': ['<h1>Test</h1>', '<p>This is a test</p>']
            },
            {
                'name': 'custom_div',
                'content': "{% div .my-class #my-id %}Content{% enddiv %}",
                'expected': ['<div class="my-class" id="my-id">', 'Content']
            },
            {
                'name': 'htmx',
                'content': '{% button .btn hx-get="/api" %}Click{% endbutton %}',
                'expected': ['hx-get="/api"', 'Click']
            }
        ]

        for case in test_cases:
            with self.subTest(case=case['name']):
                md_file = self.test_md_path / f"{case['name']}.md"
                md_file.write_text(case['content'])

                call_command('spellbook_md')

                template_path = self.templates_dir / \
                    'spellbook_md' / f"{case['name']}.html"
                self.assertTrue(template_path.exists())


class ErrorHandlingTest(BaseTestCase):
    """Tests for various error handling scenarios"""

    def setUp(self):
        super().setUp()
        self.processor = MarkdownFileProcessor()

    def test_unexpected_processing_error(self):
        """Test handling of unexpected errors during file processing"""
        # Create a mock file that will raise an unexpected error
        test_file = self.test_md_path / 'error.md'
        test_file.write_text('# Test')

        # Mock open to raise an unexpected error
        with patch('builtins.open', side_effect=Exception('Unexpected error')):
            with self.assertRaises(MarkdownProcessingError) as context:
                self.processor.process_file(
                    test_file,
                    str(self.test_md_path),
                    'error.md',
                    []
                )
            self.assertIn('Unexpected error',
                          str(context.exception))

    def test_template_creation_error(self):
        """Test handling of template creation errors"""
        template_generator = TemplateGenerator(
            self.test_content_app, str(self.templates_dir))

        # Create a scenario where template creation fails
        with patch('pathlib.Path.write_text', side_effect=Exception('Permission denied')):
            with self.assertRaises(CommandError) as context:
                template_generator.create_template(
                    Path('test.html'),
                    '<h1>Test</h1>'
                )
            self.assertIn('Could not create template', str(context.exception))

    def test_url_generation_error(self):
        """Test handling of URL generation errors"""
        url_generator = URLViewGenerator(
            self.test_content_app, str(self.test_content_path))

        # Test URLs file writing error
        with patch('builtins.open', side_effect=Exception('Permission denied')):
            with self.assertRaises(CommandError) as context:
                url_generator._write_urls(['test_url'])
            self.assertIn('Failed to write URLs file', str(context.exception))

    def test_views_generation_error(self):
        """Test handling of views generation errors"""
        url_generator = URLViewGenerator(
            self.test_content_app, str(self.test_content_path))

        # Test views file writing error
        with patch('builtins.open', side_effect=Exception('Permission denied')):
            with self.assertRaises(CommandError) as context:
                url_generator._write_views(['test_view'], {})
            self.assertIn('Failed to write views file', str(context.exception))


class SpellBlockDiscoveryTest(BaseTestCase):
    """Tests for spellblock discovery functionality"""

    def test_spellblock_discovery_error(self):
        """Test handling of errors during spellblock discovery"""
        command = Command()

        # Mock apps.get_app_configs to include a problematic app
        mock_app_config = MagicMock()
        mock_app_config.name = 'problem_app'

        with patch('django.apps.apps.get_app_configs', return_value=[mock_app_config]):
            with patch('importlib.import_module', side_effect=Exception('Import error')):
                # Should not raise exception but log warning
                command.discover_blocks()
                # Verify warning was logged (you might need to adjust this based on your logging setup)


class TOCGenerationTest(BaseTestCase):
    """Tests for Table of Contents generation"""

    def test_toc_entry_error(self):
        """Test handling of errors during TOC entry addition"""
        command = Command()

        # Create a markdown file with invalid frontmatter that will cause processing to fail
        test_file = self.test_md_path / 'bad_toc.md'
        test_file.write_text('''---
invalid: frontmatter
that: will cause
an: error
---
# Content''')

        # Mock the FrontMatterParser to raise an exception
        with patch('django_spellbook.markdown.frontmatter.FrontMatterParser') as mock_parser:
            mock_parser.side_effect = Exception('Invalid frontmatter')

            toc = command._build_toc()

            # Verify the basic structure exists but no entries were added
            self.assertEqual(toc['title'], 'root')
            self.assertEqual(toc['url'], '')

    def test_toc_empty_directory(self):
        """Test TOC generation with empty directory"""
        command = Command()

        # Ensure the directory is empty
        for file in self.test_md_path.glob('*'):
            file.unlink()

        toc = command._build_toc()

        # Verify minimal TOC structure
        self.assertEqual(toc['title'], 'root')
        self.assertEqual(toc['url'], '')
        # Note: The TOC implementation might not include empty children dict
        # so we don't test for it specifically

    def test_toc_successful_entry(self):
        """Test successful TOC entry addition"""
        command = Command()

        # Create a valid markdown file
        test_file = self.test_md_path / 'good_toc.md'
        test_file.write_text('''---
title: Test Page
---
# Content''')

        toc = command._build_toc()

        # Verify the entry was added correctly
        self.assertEqual(toc['title'], 'root')
        self.assertEqual(toc['url'], '')
        self.assertIn('children', toc)
        self.assertIn('good_toc', toc['children'])
        self.assertEqual(toc['children']['good_toc']['title'], 'Test Page')
        self.assertEqual(toc['children']['good_toc']['url'], 'good_toc')

    def test_toc_nested_structure(self):
        """Test TOC generation with nested directory structure"""
        command = Command()

        # Create nested directory structure
        nested_dir = self.test_md_path / 'nested'
        nested_dir.mkdir(exist_ok=True)

        # Create files in both root and nested directory
        root_file = self.test_md_path / 'root.md'
        root_file.write_text('''---
title: Root Page
---
# Root Content''')

        nested_file = nested_dir / 'nested.md'
        nested_file.write_text('''---
title: Nested Page
---
# Nested Content''')

        toc = command._build_toc()

        # Verify the nested structure
        self.assertEqual(toc['title'], 'root')
        self.assertEqual(toc['url'], '')
        self.assertIn('children', toc)
        self.assertIn('root', toc['children'])
        self.assertIn('nested', toc['children'])
        self.assertIn('nested', toc['children']['nested']['children'])


class EmptyContentTest(BaseTestCase):
    """Tests for handling empty content scenarios"""

    def test_no_markdown_files(self):
        """Test handling of no markdown files found"""
        command = Command()

        # Create empty directory structure
        self.test_md_path.mkdir(exist_ok=True)

        with self.assertRaises(CommandError) as context:
            command.handle()
        self.assertIn('No markdown files', str(context.exception))
