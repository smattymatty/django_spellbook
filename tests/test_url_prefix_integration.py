import os
from pathlib import Path
from io import StringIO
from unittest.mock import patch, Mock, MagicMock, call

from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError

from django_spellbook.management.commands.spellbook_md import Command
from django_spellbook.management.commands.processing.file_writer import FileWriter
from django_spellbook.management.commands.command_utils import validate_spellbook_settings
from django_spellbook.management.commands.spellbook_md_p.processor import MarkdownProcessor


class TestURLPrefixFileWriterIntegration(TestCase):
    """Test URL prefix integration with the FileWriter component."""
    
    @patch('django_spellbook.management.commands.processing.file_writer.get_spellbook_dir')
    @patch('django_spellbook.management.commands.processing.file_writer.os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists')
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_file_writer_with_empty_url_prefix(self, mock_write_file, mock_create_file, mock_open, mock_exists, mock_get_dir):
        """Test FileWriter uses empty URL prefix correctly in main urls.py."""
        # Set up mocks
        mock_get_dir.return_value = '/test/path'
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "# Empty file"
        
        # Initialize FileWriter with empty URL prefix
        file_writer = FileWriter('test_app', '')
        
        # Use more specific assertion on the write_file calls
        expected_content = "from django.urls import path, include\n\nurlpatterns = [\n    path('', include('django_spellbook.urls_test_app'))\n]\n"
        
        found_expected_content = False
        for call_args in mock_write_file.call_args_list:
            args, _ = call_args
            file_path, content = args
            if file_path.endswith('urls.py') and content == expected_content:
                found_expected_content = True
                break
        
        self.assertTrue(found_expected_content, "Expected content was not written to urls.py")
    
    @patch('django_spellbook.management.commands.processing.file_writer.get_spellbook_dir')
    @patch('django_spellbook.management.commands.processing.file_writer.os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists')
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_file_writer_with_empty_url_prefix(self, mock_write_file, mock_create_file, mock_open, mock_exists, mock_get_dir):
        """Test FileWriter uses empty URL prefix correctly in main urls.py."""
        # Set up mocks
        mock_get_dir.return_value = '/test/path'
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "# Empty file"
        
        # Initialize FileWriter with empty URL prefix
        file_writer = FileWriter('test_app', '')
        
        # Check if write_file was called with correct content
        url_file_written = False
        for call_args in mock_write_file.call_args_list:
            args, _ = call_args
            file_path, content = args
            
            if file_path.endswith('urls.py'):
                url_file_written = True
                self.assertIn("path('', include('django_spellbook.urls_test_app'))", content)
        
        self.assertTrue(url_file_written, "urls.py file was not written correctly")


class TestURLPrefixEdgeCasesIntegration(TestCase):
    """Test URL prefix edge cases in an integration context."""
    
    def test_normalize_url_prefix_single_app(self):
        """Test URL prefix normalization for a single app."""
        with self.settings(
            SPELLBOOK_MD_PATH='/test/path',
            SPELLBOOK_MD_APP='test_app',
            SPELLBOOK_MD_URL_PREFIX='/prefix/',  # With leading and trailing slashes
            SPELLBOOK_MD_BASE_TEMPLATE="template"
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # Prefix should have slashes removed
            self.assertEqual(url_prefixes, ['prefix'])
            self.assertEqual(base_templates, ['template'])
            
    def test_normalize_base_templates_unequal_lengths(self):
        """Test normalization of base templates with unequal lengths."""
        with self.settings(
            SPELLBOOK_MD_PATH='/test/path',
            SPELLBOOK_MD_APP='test_app',
            SPELLBOOK_MD_BASE_TEMPLATE=['template1', None, 'template2']  # None and empty strings
        ):
            with self.assertRaises(CommandError):
                md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()

            
    
    def test_normalize_url_prefixes_multi_app(self):
        """Test URL prefix normalization for multiple apps."""
        with self.settings(
            SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
            SPELLBOOK_MD_APP=['app1', 'app2', 'app3'],
            SPELLBOOK_MD_URL_PREFIX=['/prefix1/', '//prefix2//', '/prefix3']  # Various slash patterns
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # All prefixes should have slashes removed
            self.assertEqual(url_prefixes, ['prefix1', 'prefix2', 'prefix3'])
            self.assertEqual(base_templates, [None, None, None])
            
    def test_string_base_template_for_multi_app(self):
        """Test base template normalization for multiple apps."""
        with self.settings(
            SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
            SPELLBOOK_MD_APP=['app1', 'app2', 'app3'],
            SPELLBOOK_MD_BASE_TEMPLATE='template1'  # Single string for multiple apps
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # All templates should be strings
            self.assertEqual(base_templates, ['template1', 'template1', 'template1'])
    
    def test_string_url_prefix_for_multi_app_error(self):
        """Test error when providing a string URL prefix for multiple apps."""
        with self.settings(
            SPELLBOOK_MD_PATH=['/path1', '/path2'],
            SPELLBOOK_MD_APP=['app1', 'app2'],
            SPELLBOOK_MD_URL_PREFIX='shared-prefix'  # Single string for multiple apps
        ):
            with self.assertRaises(CommandError) as context:
                validate_spellbook_settings()
            
            self.assertIn("must have the same number of entries", str(context.exception))
    
    def test_empty_url_prefixes(self):
        """Test with empty string URL prefixes."""
        with self.settings(
            SPELLBOOK_MD_PATH=['/path1', '/path2'],
            SPELLBOOK_MD_APP=['app1', 'app2'],
            SPELLBOOK_MD_URL_PREFIX=['', '']  # Empty prefixes
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # Empty prefixes should be preserved
            self.assertEqual(url_prefixes, ['', ''])
            self.assertEqual(base_templates, [None, None])


class TestURLPrefixDefaultsIntegration(TestCase):
    """Test default URL prefix behavior in various configurations."""
    
    def test_default_url_prefix_single_app(self):
        """Test default URL prefix for a single app."""
        with self.settings(
            SPELLBOOK_MD_PATH='/test/path',
            SPELLBOOK_MD_APP='test_app'
            # No SPELLBOOK_MD_URL_PREFIX specified
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # Single app should get empty prefix by default
            self.assertEqual(url_prefixes, [''])
    
    def test_default_url_prefixes_multi_app(self):
        """Test default URL prefixes for multiple apps."""
        with self.settings(
            SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
            SPELLBOOK_MD_APP=['app1', 'app2', 'app3']
            # No SPELLBOOK_MD_URL_PREFIX specified
        ):
            md_paths, content_apps, url_prefixes, base_templates = validate_spellbook_settings()
            
            # First app gets empty prefix, others get app name
            self.assertEqual(url_prefixes, ['', 'app2', 'app3'])