import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
from django.core.management.base import CommandError
from django.test import TestCase
from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.utils import get_clean_url


class TestURLViewGenerator(TestCase):
    def setUp(self):
        self.generator = URLViewGenerator('test_app', '/test/path')
        self.mock_context = Mock(spec=SpellbookContext)
        self.mock_context.__dict__ = {'title': 'Test', 'toc': {}}

        # Create a sample processed file
        self.processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=self.mock_context
        )

    def test_initialization(self):
        """Test URLViewGenerator initialization."""
        self.assertEqual(self.generator.content_app, 'test_app')
        self.assertEqual(self.generator.content_dir_path, '/test/path')
        self.assertTrue(hasattr(self.generator, 'spellbook_dir'))

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_ensure_urls_views_files_creation(self, mock_file, mock_exists):
        """Test creation of app-specific URLs and views files."""
        mock_exists.return_value = False

        self.generator._ensure_urls_views_files()

        # Should create app-specific files and main urls.py
        urls_module = f"urls_test_app"
        views_module = f"views_test_app"
        
        mock_file.assert_any_call(
            f"{self.generator.spellbook_dir}/{urls_module}.py", 'w')
        mock_file.assert_any_call(
            f"{self.generator.spellbook_dir}/{views_module}.py", 'w')
        mock_file.assert_any_call(
            f"{self.generator.spellbook_dir}/urls.py", 'w')

    def test_generate_view_name(self):
        """Test view name generation from URL pattern."""
        url_pattern = 'docs/getting-started/index'
        # Update expected value without 'view_' prefix
        expected = 'docs_getting_started_index'

        result = self.generator._generate_view_name(url_pattern)

        self.assertEqual(result, expected)

    def test_get_template_path(self):
        """Test template path generation."""
        relative_url = 'docs/index'
        expected = 'test_app/spellbook_md/docs/index.html'

        result = self.generator._get_template_path(relative_url)

        self.assertEqual(result, expected)

    def test_prepare_context_dict(self):
        """Test context dictionary preparation."""
        context = Mock(spec=SpellbookContext)
        context.__dict__ = {
            'title': 'Test',
            'date': '2023-01-01',
            'toc': {'some': 'data'}
        }

        result = self.generator._prepare_context_dict(context)

        self.assertNotIn('toc', result)
        self.assertEqual(result['title'], 'Test')

    @patch('builtins.open', new_callable=mock_open)
    def test_write_urls(self, mock_file):
        """Test writing URL patterns to file."""
        urls = ["path('test', views.view_test, name='view_test')"]

        self.generator._write_urls(urls)

        mock_file.assert_called_once()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn('urlpatterns = [', written_content)
        self.assertIn("path('test'", written_content)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_urls_with_dashes(self, mock_file):
        """Test writing URL patterns to file with dashes in URLs."""
        urls = ["path('--test', views.view_test, name='view_test')"]

        self.generator._write_urls(urls)

        mock_file.assert_called_once()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn('urlpatterns = [', written_content)
        self.assertIn("path('test'", written_content)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_urls_with_dashes_in_multiple_parts(self, mock_file):
        """Test writing URL patterns to file with dashes in multiple parts."""
        urls = [
            "path('--test-name/--test-name-2', views.view_test, name='view_test')",
        ]

        self.generator._write_urls(urls)

        mock_file.assert_called_once()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn('urlpatterns = [', written_content)
        self.assertIn("path('test-name/test-name-2'", written_content)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_views(self, mock_file):
        """Test writing view functions to file."""
        views = [
            "def view_test(request):\n    return render(request, 'test.html', {})"]
        toc = {'test': {'title': 'Test'}}

        self.generator._write_views(views, toc)

        mock_file.assert_called_once()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn('from django.shortcuts import render', written_content)
        self.assertIn('TOC = ', written_content)

    @patch.object(URLViewGenerator, '_write_urls')
    @patch.object(URLViewGenerator, '_write_views')
    def test_generate_urls_and_views(self, mock_write_views, mock_write_urls):
        """Test full URL and view generation process."""
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test',
            context=self.mock_context
        )

        self.generator.generate_urls_and_views([processed_file], {})

        mock_write_urls.assert_called_once()
        mock_write_views.assert_called_once()

    def test_create_file_if_not_exists_error(self):
        """Test file creation error handling"""
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.side_effect = IOError("Permission denied")

                with self.assertRaises(CommandError) as context:
                    self.generator._create_file_if_not_exists(
                        'test.py', 'content')

                self.assertIn("Failed to create test.py",
                              str(context.exception))

    def test_generate_urls_and_views_error(self):
        """Test error handling in generate_urls_and_views"""
        with patch.object(self.generator, '_generate_url_data') as mock_generate:
            mock_generate.side_effect = Exception("Generation error")

            with self.assertRaises(CommandError) as context:
                self.generator.generate_urls_and_views(
                    [self.processed_file], {})

            self.assertIn("Failed to generate URLs and views",
                          str(context.exception))

    def test_write_urls_error(self):
        """Test error handling in _write_urls"""
        with patch.object(self.generator, '_write_file') as mock_write:
            mock_write.side_effect = Exception("Write error")

            with self.assertRaises(CommandError) as context:
                self.generator._write_urls(['test_url'])

            self.assertIn("Failed to write URLs file", str(context.exception))

    def test_write_views_error(self):
        """Test error handling in _write_views"""
        with patch.object(self.generator, '_write_file') as mock_write:
            mock_write.side_effect = Exception("Write error")

            with self.assertRaises(CommandError) as context:
                self.generator._write_views(['test_view'], {})

            self.assertIn("Failed to write views file", str(context.exception))

    def test_write_file_error(self):
        """Test error handling in _write_file"""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Write permission denied")

            with self.assertRaises(CommandError) as context:
                self.generator._write_file('test.py', 'content')

            self.assertIn("Failed to write test.py", str(context.exception))

    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_ensure_urls_views_files_multiple_errors(self, mock_abspath, mock_exists):
        """Test handling of multiple file creation errors"""
        mock_abspath.return_value = '/test/path'
        mock_exists.return_value = False

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Multiple errors")

            with self.assertRaises(CommandError) as context:
                self.generator._ensure_urls_views_files()

            self.assertIn("Failed to create", str(context.exception))

    def test_generate_url_data_error(self):
        """Test error handling in _generate_url_data with invalid processed file"""
        invalid_processed_file = Mock(spec=ProcessedFile)
        invalid_processed_file.relative_url = None  # This should cause an error

        with self.assertRaises(AttributeError):
            self.generator._generate_url_data(invalid_processed_file)

    def test_prepare_context_dict_error(self):
        """Test error handling in _prepare_context_dict with invalid context"""
        invalid_context = Mock(spec=SpellbookContext)
        invalid_context.__dict__ = {'toc': {}, 'date': 'invalid-date'}

        # Should not raise an exception but handle the invalid date gracefully
        result = self.generator._prepare_context_dict(invalid_context)
        self.assertNotIn('toc', result)

    @patch('os.path.abspath')
    def test_get_spellbook_dir_error(self, mock_abspath):
        """Test error handling in _get_spellbook_dir"""
        mock_abspath.side_effect = Exception("Path error")

        with self.assertRaises(Exception) as context:
            self.generator._get_spellbook_dir()

        self.assertIn("Path error", str(context.exception))

    def test_generate_views_file_content_error_with_invalid_toc(self):
        """Test error handling in _generate_views_file_content with invalid TOC types"""
        # Test with a TOC that can't be string-formatted
        class CustomObject:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        invalid_toc = CustomObject()

        with self.assertRaises(ValueError):
            self.generator._generate_views_file_content(
                ['test_view'], invalid_toc)

    def test_generate_views_file_content_with_invalid_views(self):
        """Test _generate_views_file_content with invalid views list"""
        # Test with invalid views content
        invalid_views = [None, 123, object()]

        with self.assertRaises(TypeError):
            self.generator._generate_views_file_content(invalid_views, {})

    def test_generate_view_name_with_dashes(self):
        """Test view name generation with dashes in URL pattern."""
        url_pattern = '--view-name'
        expected = '__view_name'

        result = self.generator._generate_view_name(url_pattern)

        self.assertEqual(result, expected)

    def test_get_clean_url(self):
        """Test URL cleaning"""
        url = '--test-url/--test-url-2/---test-url-3'
        expected = 'test-url/test-url-2/test-url-3'

        result = get_clean_url(url)

        self.assertEqual(result, expected)

    @patch('os.path.join')
    def test_get_template_path_error(self, mock_join):
        """Test error handling in _get_template_path"""
        mock_join.side_effect = Exception("Path join error")

        with self.assertRaises(Exception):
            self.generator._get_template_path("test/url")

    def test_generate_view_name_error(self):
        """Test error handling in _generate_view_name with invalid input"""
        invalid_url = None

        with self.assertRaises(AttributeError):
            self.generator._generate_view_name(invalid_url)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="urlpatterns = []")
    def test_update_main_urls_file(self, mock_file, mock_exists):
        """Test updating the main urls.py to include app-specific URL modules."""
        mock_exists.return_value = True

        self.generator._update_main_urls_file()
        
        # Verify main urls.py was updated with the app inclusion
        mock_file.assert_any_call(f"{self.generator.spellbook_dir}/urls.py", 'w')
        written_content = mock_file().write.call_args[0][0]
        
        # Should contain path to include the app-specific URL module
        self.assertIn(f"include('django_spellbook.urls_test_app')", written_content)
        self.assertIn(f"path('test_app/'", written_content)
            
    def test_app_specific_file_generation(self):
        """Test generation of app-specific urls and views files."""
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test',
            context=self.mock_context
        )
        
        with patch.object(self.generator, '_write_file') as mock_write:
            self.generator.generate_urls_and_views([processed_file], {})
            
            # Should write to app-specific files
            urls_module = f"urls_test_app.py"
            views_module = f"views_test_app.py"
            
            # Check that app-specific files were written to
            mock_write.assert_any_call(urls_module, unittest.mock.ANY)
            mock_write.assert_any_call(views_module, unittest.mock.ANY)
            
    
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('django_spellbook.management.commands.processing.url_view_generator.logger')
    def test_exception_handling_in_update_main_urls(self, mock_logger, mock_open, mock_exists):
        """Test exception handling when reading the urls.py file"""
        # Set up conditions for exception
        mock_exists.return_value = True
        
        # Make open raise an exception when trying to read the file
        file_mock = mock_open.return_value.__enter__.return_value
        file_mock.read.side_effect = IOError("Test file read error")
        
        # Call the method - should not raise the exception
        self.generator._update_main_urls_file()
        
        # Verify logger.error was called with the right message
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Error reading urls.py", error_msg)
        self.assertIn("Test file read error", error_msg)
        
        # Verify the method continued execution and wrote the file
        # There should be a second call to open in write mode
        self.assertEqual(mock_open.call_count, 2)
        calls = mock_open.call_args_list
        self.assertEqual(calls[0][0][1], 'r')  # First call should be in read mode
        self.assertEqual(calls[1][0][1], 'w')  # Second call should be in write mode
        

import os
import shutil
import tempfile
import datetime




class URLViewGeneratorIntegrationTest(TestCase):
    """Integration tests for URL name generation in URLViewGenerator"""
    
    def setUp(self):
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a temporary spellbook directory structure
        self.spellbook_dir = os.path.join(self.temp_dir, 'django_spellbook')
        os.makedirs(self.spellbook_dir, exist_ok=True)
        
        # Set up the generator with a real filesystem
        self.generator = URLViewGenerator('test_app', os.path.join(self.temp_dir, 'content'))
        
        # Override the spellbook directory to use our temporary one
        self.generator.spellbook_dir = self.spellbook_dir
        
        # Create a mock context for processed files
        self.context = SpellbookContext(
            title='Test',
            created_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            updated_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            url_path='test',
            raw_content='# Test\nThis is a test',
        )
        
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def _create_processed_file(self, relative_url):
        """Helper to create a processed file with a specific relative URL"""
        return ProcessedFile(
            original_path=Path(f"/test/{relative_url}.md"),
            html_content="<h1>Test</h1>",
            template_path=Path(f"/test/templates/{relative_url}.html"),
            relative_url=relative_url,
            context=self.context
        )
    
    def test_actual_urls_file_generation(self):
        """Test the actual generation of the urls.py file with proper URL names"""
        # Process multiple files with different path structures
        processed_files = [
            self._create_processed_file("first_blog"),
            self._create_processed_file("lifestyle/digital-minimalism"),
            self._create_processed_file("blocks/practice"),
            self._create_processed_file("blocks/quote"),
            self._create_processed_file("tech/sustainable-tech")
        ]
        
        # Generate URLs and views
        self.generator.generate_urls_and_views(processed_files, {})
        
        # Read the generated urls.py file
        urls_file_path = os.path.join(self.spellbook_dir, 'urls_test_app.py')
        self.assertTrue(os.path.exists(urls_file_path), "URLs file was not created")
        
        with open(urls_file_path, 'r') as f:
            urls_content = f.read()
        
        # Verify URL patterns have correct names
        self.assertIn("path('first_blog/', first_blog, name='first_blog')", urls_content)
        self.assertIn("path('lifestyle/digital-minimalism/', lifestyle_digital_minimalism, name='lifestyle_digital-minimalism')", urls_content)
        self.assertIn("path('blocks/practice/', blocks_practice, name='blocks_practice')", urls_content)
        self.assertIn("path('blocks/quote/', blocks_quote, name='blocks_quote')", urls_content)
        self.assertIn("path('tech/sustainable-tech/', tech_sustainable_tech, name='tech_sustainable-tech')", urls_content)