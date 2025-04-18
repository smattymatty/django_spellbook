# django_spellbook/tests/test_spellbook_md_integration.py

import unittest
from unittest.mock import patch, Mock, MagicMock
from io import StringIO

from django.test import TestCase
from django.core.management import call_command

from django_spellbook.management.commands.spellbook_md import (
    Command, ConfigurationError, ContentDiscoveryError, ProcessingError
)

class TestSpellbookMDIntegration(TestCase):
    """Integration tests for the spellbook_md command."""
    
    def test_basic_functionality(self):
        """Test basic command functionality with a single source-destination pair."""
        # Use a context manager approach for more precise control over patching
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
             patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
             patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
             patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'])
            mock_find_files.return_value = [('/test/path', 'test.md')]
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Setup processor mock
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            mock_processor.process_file.return_value = MagicMock()  # Mock a successful processed file
            mock_processor_class.return_value = mock_processor
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn('Found 1 markdown files to process', output)
            self.assertIn('Successfully processed 1 files for test_app', output)
            
            # Verify correct method calls
            mock_validate.assert_called_once()
            mock_find_files.assert_called_once_with('/test/path')
            mock_setup.assert_called_once_with('test_app', '/test/path')
            mock_processor.build_toc.assert_called_once()
            mock_processor.process_file.assert_called_once_with('/test/path', 'test.md', {})
            mock_processor.generate_urls_and_views.assert_called_once()
    
    def test_multiple_sources(self):
        """Test processing multiple source-destination pairs."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'])
            
            # Use call count tracking to ensure correct behavior for each call
            find_files_calls = 0
            def find_files_side_effect(path):
                nonlocal find_files_calls
                result = []
                if find_files_calls == 0:
                    result = [('/path1', 'file1.md'), ('/path1', 'file2.md')]
                else:
                    result = [('/path2', 'file3.md')]
                find_files_calls += 1
                return result
            
            mock_find_files.side_effect = find_files_side_effect
            
            # Track setup calls similarly
            setup_calls = 0
            def setup_side_effect(app, path):
                nonlocal setup_calls
                result = None
                if setup_calls == 0:
                    result = ('/app1/path', '/app1/templates')
                else:
                    result = ('/app2/path', '/app2/templates')
                setup_calls += 1
                return result
            
            mock_setup.side_effect = setup_side_effect
            
            # Track processor creation
            processor_calls = 0
            def processor_factory(**kwargs):
                nonlocal processor_calls
                processor = MagicMock()
                processor.build_toc.return_value = {}
                
                if processor_calls == 0:
                    # First processor processes 2 files
                    processor.process_file.side_effect = [MagicMock(), MagicMock()]
                else:
                    # Second processor processes 1 file
                    processor.process_file.return_value = MagicMock()
                
                processor_calls += 1
                return processor
            
            mock_processor_class.side_effect = processor_factory
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn('Found 2 markdown files to process', output)  # First source
            self.assertIn('Found 1 markdown files to process', output)  # Second source
            self.assertIn('Successfully processed 2 files for app1', output)
            self.assertIn('Successfully processed 1 files for app2', output)
    
    def test_continue_on_error(self):
        """Test --continue-on-error flag allows processing to continue after file errors."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'])
            mock_find_files.return_value = [
                ('/test/path', 'good.md'),
                ('/test/path', 'bad.md')
            ]
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Setup processor mock with a file that succeeds and one that fails
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            
            # Configure process_file to succeed for good.md but fail for bad.md
            def process_file_side_effect(dirpath, filename, toc):
                if filename == 'bad.md':
                    raise ProcessingError("Error processing file")
                return MagicMock()  # Return a mock for successful file
            
            mock_processor.process_file.side_effect = process_file_side_effect
            mock_processor_class.return_value = mock_processor
            
            # Run the command with continue-on-error flag
            out = StringIO()
            call_command('spellbook_md', continue_on_error=True, stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn('Error processing file bad.md', output)
            self.assertIn('Successfully processed 1 files for test_app', output)
            
            # Verify both files were attempted
            self.assertEqual(mock_processor.process_file.call_count, 2)
            mock_processor.generate_urls_and_views.assert_called_once()
        
    def test_error_in_second_source(self):
        """Test handling errors in second source while continuing processing."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'])
            
            # Track find_files calls to return different values
            find_files_calls = 0
            def find_files_side_effect(path):
                nonlocal find_files_calls
                result = []
                if find_files_calls == 0:
                    result = [('/path1', 'file1.md'), ('/path1', 'file2.md')]
                # Second call returns empty list (no files found)
                find_files_calls += 1
                return result
            
            mock_find_files.side_effect = find_files_side_effect
            
            # Only first setup will be called
            mock_setup.return_value = ('/app1/path', '/app1/templates')
            
            # Only first processor is created
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            mock_processor.process_file.side_effect = [MagicMock(), MagicMock()]
            mock_processor_class.return_value = mock_processor
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn('Found 2 markdown files to process', output)  # First source
            self.assertIn('Successfully processed 2 files for app1', output)
            self.assertIn('Error processing pair', output)  # Error for second pair
            self.assertIn('No markdown files found', output)  # Specific error message
            self.assertIn('1 of 2 pairs processed successfully', output)  # Summary
        
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    def test_configuration_error(self, mock_validate):
        """Test handling of configuration errors."""
        # Setup mock to raise error
        mock_validate.side_effect = ConfigurationError("Missing required settings")
        
        # Run command
        out = StringIO()
        with self.assertRaises(ConfigurationError):
            call_command('spellbook_md', stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Configuration error', output)
        self.assertIn('Please check your Django settings.py file', output)