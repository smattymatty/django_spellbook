# django_spellbook/tests/test_spellbook_md_command.py

import unittest
from unittest.mock import patch, Mock, call, MagicMock
from pathlib import Path
from io import StringIO
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django_spellbook.management.commands.spellbook_md import Command
from django.core.management import call_command
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

class TestSpellbookMDCommand(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.command = Command()
        self.command.stdout = Mock()  # Mock stdout for testing output

    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_basic_execution(self, mock_process_pair, mock_validate, mock_discover):
        """Test basic successful execution of the command"""
        # Set up mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        # _process_source_destination_pair now returns (count, processed_files)
        mock_process_pair.return_value = (5, [])

        # Execute command
        self.command.handle()

        # Verify blocks were discovered
        mock_discover.assert_called_once_with(self.command.reporter)

        # Verify settings were validated
        mock_validate.assert_called_once()

        # Verify processing was called with correct arguments
        mock_process_pair.assert_called_once_with('/test/path', 'test_app', 'test_prefix', None, None)
        

    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_multiple_pairs(self, mock_process_pair, mock_validate, mock_discover):
        """Test handling of multiple source-destination pairs"""
        # Set up mocks
        mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'], ['test', ''], [None, None], [None, None])
        # _process_source_destination_pair now returns (count, processed_files)
        mock_process_pair.return_value = (5, [])

        # Execute command
        self.command.handle()

        # Verify processing was called twice with correct arguments
        expected_calls = [
            call('/path1', 'app1', 'test', None, None),
            call('/path2', 'app2', '', None, None)
        ]
        self.assertEqual(mock_process_pair.call_count, 2)
        mock_process_pair.assert_has_calls(expected_calls)
    
    # test_handle_multiple_pairs_with_identical_url_prefix(self, mock_process_pair, mock_validate, mock_discover):
        """Test handling of multiple source-destination pairs with identical URL prefixes Should Raise an error is duplicate URL prefixes are found"""
    #    pass

    # In test_handle_error_single_pair
    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_error_single_pair(self, mock_process_pair, mock_validate, mock_discover):
        """Test error handling with a single pair (should raise)"""
        # Set up mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], ["template"], [None])
        
        # Set up error
        test_error = CommandError("Test processing error")
        mock_process_pair.side_effect = test_error
        
        # Execute command - should raise the error
        with self.assertRaises(CommandError) as context:
            self.command.handle()
        
        # Verify it's the same error
        self.assertEqual(str(context.exception), "Test processing error")
        


    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_error_multiple_pairs(self, mock_process_pair, mock_validate, mock_discover):
        """Test error handling with multiple pairs (should continue)"""
        # Set up mocks
        mock_validate.return_value = (
            ['/path1', '/path2', '/path3'], ['app1', 'app2', 'app3'], ['test_prefix', 'gg', ''], [None, 'Template', None], [None, None, None]
            )
        
        # Set up error for the second pair
        def side_effect(path, app, url_prefix, base_template, extend_from=None):
            if path == '/path2':
                raise CommandError("Test processing error")
            return 1  # Return an integer count on success (not None)
        
        mock_process_pair.side_effect = side_effect
        
        # Execute command
        self.command.handle()
        
        # Verify all pairs were attempted
        expected_calls = [
            call('/path1', 'app1', 'test_prefix', None, None),
            call('/path2', 'app2', 'gg', "Template", None),
            call('/path3', 'app3', '', None, None)
        ]
        self.assertEqual(mock_process_pair.call_count, 3)
        mock_process_pair.assert_has_calls(expected_calls)
        

    
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_process_pair_no_files(self, mock_find_files):
        """Test error when no markdown files are found"""
        # Set up mock
        mock_find_files.return_value = []
        # add reporter to command
        self.command.reporter = MarkdownReporter(self.command.stdout)
        # Execute and test
        with self.assertRaises(CommandError) as context:
            self.command._process_source_destination_pair('/test/path', 'test_app', 'test_prefix', None, None)
        
        self.assertIn("No markdown files found", str(context.exception))
        mock_find_files.assert_called_once_with('/test/path')

    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_pair_successful(self, mock_processor_class, mock_setup, mock_find_files):
        """Test successful processing of a source-destination pair"""
        # Set up mocks
        mock_find_files.return_value = [('/test/path', 'file1.md'), ('/test/path', 'file2.md')]
        mock_setup.return_value = ('/content/dir/path', '/template/dir')
        
        # Create mock processor instance
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {'toc': 'data'}
        
        # Create mock processed files
        mock_processed_file1 = Mock()
        mock_processed_file2 = Mock()
        mock_processor.process_file.side_effect = [mock_processed_file1, mock_processed_file2]
        
        mock_processor_class.return_value = mock_processor
        # add reporter to command
        self.command.reporter = MarkdownReporter(self.command.stdout)
        # Execute
        self.command._process_source_destination_pair('/test/path', 'test_app', 'test_prefix', None, None)
        
        # Verify processor was initialized correctly!
        mock_processor_class.assert_called_once_with(
            content_app='test_app',
            source_path='/test/path',
            content_dir_path='/content/dir/path',
            template_dir='/template/dir',
            reporter=self.command.reporter,
            url_prefix='test_prefix',
            base_template=None,
            extend_from=None
        )
        
        # Verify TOC was built
        mock_processor.build_toc.assert_called_once()
        
        # Verify files were processed
        self.assertEqual(mock_processor.process_file.call_count, 2)
        mock_processor.process_file.assert_has_calls([
            call('/test/path', 'file1.md', {'toc': 'data'}),
            call('/test/path', 'file2.md', {'toc': 'data'})
        ])
        
        # Verify URLs and views were generated
        mock_processor.generate_urls_and_views.assert_called_once_with(
            [mock_processed_file1, mock_processed_file2], 
            {'toc': 'data'}
        )
        
        # Verify output messages
        self.command.stdout.write.assert_any_call("Found 2 markdown files to process")
        self.command.stdout.write.assert_any_call("Processing file 1/2: file1.md")
        self.command.stdout.write.assert_any_call("Processing file 2/2: file2.md")
        self.command.stdout.write.assert_any_call("Generating URLs and views...")


    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_pair_file_processing_error(self, mock_processor_class, mock_setup, mock_find_files):
        """Test error handling when file processing fails"""
        # Set up mocks
        mock_find_files.return_value = [('/test/path', 'file1.md'), ('/test/path', 'file2.md')]
        mock_setup.return_value = ('/content/dir/path', '/template/dir')
        
        # Create mock processor instance
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {'toc': 'data'}
        # Make process_file return None (indicating failure) for all files
        mock_processor.process_file.return_value = None
        mock_processor_class.return_value = mock_processor
        self.command.reporter = MarkdownReporter(self.command.stdout)
        # Execute and test
        with self.assertRaises(CommandError) as context:
            self.command._process_source_destination_pair('/test/path', 'test_app', 'test_prefix', None, None)
        
        self.assertIn("No markdown files were processed successfully", str(context.exception))
        
        # Verify files were attempted to be processed
        self.assertEqual(mock_processor.process_file.call_count, 2)
        
        # Verify URLs and views were not generated
        mock_processor.generate_urls_and_views.assert_not_called()

    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_pair_partial_file_processing_success(self, mock_processor_class, mock_setup, mock_find_files):
        """Test handling when some files process successfully and others fail"""
        # Set up mocks
        mock_find_files.return_value = [
            ('/test/path', 'file1.md'), 
            ('/test/path', 'file2.md'), 
            ('/test/path', 'file3.md')
        ]
        mock_setup.return_value = ('/content/dir/path', '/template/dir')
        
        # Create mock processor instance
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {'toc': 'data'}
        
        # Create mock processed file (only the second file succeeds)
        mock_processed_file = Mock()
        mock_processor.process_file.side_effect = [None, mock_processed_file, None]
        mock_processor_class.return_value = mock_processor
        
        # add reporter to command
        self.command.reporter = MarkdownReporter(self.command.stdout)
        # Execute
        self.command._process_source_destination_pair('/test/path', 'test_app', 'test_prefix', 'template2/path', None)
        
        # Verify all files were attempted
        self.assertEqual(mock_processor.process_file.call_count, 3)
        
        # Verify URLs and views were generated with only the successful file
        mock_processor.generate_urls_and_views.assert_called_once_with(
            [mock_processed_file], 
            {'toc': 'data'}
        )

    # In test_handle_overall_error
    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    def test_handle_overall_error(self, mock_validate, mock_discover):
        """Test error handling in the overall handle method"""
        # Set up an error in validation
        mock_validate.side_effect = CommandError("Invalid settings")
        
        # Execute command - should raise the error
        with self.assertRaises(CommandError) as context:
            self.command.handle()
        
        # Verify it's the same error
        self.assertIn("Invalid settings", str(context.exception))
        
  
# django_spellbook/tests/test_spellbook_md_exceptions.py

import unittest
from unittest.mock import patch, Mock, call
from pathlib import Path
from django.test import TestCase, override_settings

from django_spellbook.management.commands.spellbook_md import (
    Command, 
    ConfigurationError,
    ContentDiscoveryError,
    ProcessingError,
    OutputGenerationError
)

class TestSpellbookMDExceptions(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.command = Command()
        self.mock_reporter = Mock()
    
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    def test_configuration_error(self, mock_validate, mock_reporter_class):
        """Test error handling for configuration errors"""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Simulate a configuration error
        mock_validate.side_effect = Exception("Missing required settings")
        
        # Execute command - should raise the error
        with self.assertRaises(ConfigurationError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("Settings validation failed", str(context.exception))
        
        # Verify reporter was called with correct messages
        self.mock_reporter.error.assert_any_call("Configuration error: Missing required settings")
        self.mock_reporter.write.assert_any_call(
            "Please check your Django settings.py file and ensure "
            "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP are correctly configured."
        )
    
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_content_discovery_error_no_files(self, mock_find_files, mock_validate, mock_reporter_class):
        """Test error handling when no markdown files are found"""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = []
        
        # Execute command - should raise the error
        with self.assertRaises(ContentDiscoveryError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("No markdown files found", str(context.exception))
        
        # Verify reporter was called with correct messages
        self.mock_reporter.error.assert_any_call("No markdown files found in /test/path")
        self.mock_reporter.write.assert_any_call(
            "Make sure the directory exists and contains .md files."
        )
    
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    def test_configuration_error_directory_setup(self, mock_setup, mock_find_files, mock_validate, mock_reporter_class):
        """Test error handling for directory setup failures"""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'test.md')]
        mock_setup.side_effect = OSError("Permission denied")
        
        # Execute command - should raise the error
        with self.assertRaises(ConfigurationError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("Failed to set up directory structure", str(context.exception))
        self.assertIn("Permission denied", str(context.exception))
        
        # Verify reporter was called with correct messages
        self.mock_reporter.error.assert_any_call("Directory setup error: Permission denied")
        self.mock_reporter.write.assert_any_call(
            "Check that the content app exists and is correctly configured in your Django project."
        )
    
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_toc_error_continues_processing(self, mock_processor_class, mock_setup, mock_find_files, 
                                           mock_validate, mock_reporter_class):
        """Test error handling for TOC building failures"""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['wumbo'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'test.md')]
        mock_setup.return_value = ('/test/path/app', '/test/path/app/templates')
        
        # Create a mock processor with a failing build_toc method
        mock_processor = Mock()
        mock_processor.build_toc.side_effect = Exception("TOC error")
        mock_processor.process_file.return_value = Mock()  # Process succeeds
        mock_processor_class.return_value = mock_processor
        
        # Execute command
        self.command.handle()
        
        # Verify the command continued with an empty TOC
        mock_processor.process_file.assert_called_once()
        
        # Verify reporter was called with warning
        self.mock_reporter.warning.assert_any_call(
            "Error building table of contents: TOC error. "
            "Processing will continue but navigation links may not work correctly."
        )
    
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_continue_on_error_flag(self, mock_processor_class, mock_setup, mock_find_files, 
                                   mock_validate, mock_reporter_class):
        """Test --continue-on-error flag allows processing to continue after file errors"""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [
            ('/test/path', 'good.md'),
            ('/test/path', 'bad.md')
        ]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock where one file succeeds and one fails
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        
        # First file succeeds, second file raises an error
        mock_processed_file = Mock()
        
        # Use side_effect as a list to return a value for the first call and raise exception for the second
        def side_effect(dirpath, filename, toc):
            if filename == 'good.md':
                return mock_processed_file
            else:
                raise Exception("Error processing file")
        
        mock_processor.process_file.side_effect = side_effect
        mock_processor.generate_urls_and_views.return_value = None
        mock_processor_class.return_value = mock_processor
        
        # Pass the continue_on_error flag using options
        options = {'continue_on_error': True}
        self.command.handle(**options)
        
        # Verify both files were attempted
        self.assertEqual(mock_processor.process_file.call_count, 2)
        
        # Verify URLs and views were generated with the successful file
        mock_processor.generate_urls_and_views.assert_called_once()
        
        # Verify reporter called with error for the bad file
        self.mock_reporter.error.assert_any_call("Error processing file bad.md: Error processing file")
        
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_processor_initialization_error_detailed(self, mock_processor_class, mock_setup, 
                                                mock_find_files, mock_validate, mock_reporter_class):
        """Test detailed error handling when the MarkdownProcessor fails to initialize."""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'test.md')]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Simulate MarkdownProcessor initialization failure
        specific_error = ValueError("Invalid URL prefix format")
        mock_processor_class.side_effect = specific_error
        
        # Execute command - should raise a ProcessingError
        with self.assertRaises(ProcessingError) as context:
            self.command.handle()
        
        # Verify error message contains both the wrapper message and the original error
        error_msg = str(context.exception)
        self.assertIn("Failed to initialize markdown processor", error_msg)
        self.assertIn("Invalid URL prefix format", error_msg)
        
        # Verify no other processor methods were called
        mock_processor_class.assert_called_once_with(
            content_app='test_app',
            source_path='/test/path',
            content_dir_path='/content/path',
            template_dir='/template/path',
            url_prefix='test_prefix',
            base_template=None,
            extend_from=None,
            reporter=self.command.reporter
        )

    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_file_returns_none(self, mock_processor_class, mock_setup, 
                                    mock_find_files, mock_validate, mock_reporter_class):
        """Test handling when processor.process_file returns None (file not processed successfully)."""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'file1.md'), ('/test/path', 'file2.md')]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock that returns None for all process_file calls
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        mock_processor.process_file.return_value = None  # Return None to indicate file not processed
        mock_processor_class.return_value = mock_processor
        
        # Execute command - should raise a ProcessingError since no files were processed
        with self.assertRaises(ProcessingError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("No markdown files were processed successfully for test_app", str(context.exception))
        
        # Verify reporter was called with warnings for both files
        self.mock_reporter.warning.assert_any_call("File not processed: file1.md")
        self.mock_reporter.warning.assert_any_call("File not processed: file2.md")
        
        # Verify appropriate error message was reported
        self.mock_reporter.error.assert_any_call(
            "No markdown files were processed successfully for test_app"
        )
        self.mock_reporter.write.assert_any_call(
            "Check the markdown syntax and structure of your files, and ensure all required SpellBlocks are available."
        )
        
        # Verify generate_urls_and_views was not called
        mock_processor.generate_urls_and_views.assert_not_called()

    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_file_exception_with_continue_flag(self, mock_processor_class, mock_setup, 
                                                    mock_find_files, mock_validate, mock_reporter_class):
        """Test handling when process_file raises an exception but continue_on_error is True."""
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [
            ('/test/path', 'good1.md'),
            ('/test/path', 'error.md'),
            ('/test/path', 'good2.md')
        ]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock with mixed results
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        
        good_file1 = Mock()
        good_file2 = Mock()
        
        # First and third file succeed, second file raises exception
        def process_file_side_effect(dirpath, filename, toc):
            if filename == 'error.md':
                raise ValueError("Invalid markdown syntax")
            return good_file1 if filename == 'good1.md' else good_file2
        
        mock_processor.process_file.side_effect = process_file_side_effect
        mock_processor_class.return_value = mock_processor
        
        # Execute command with continue_on_error flag
        options = {'continue_on_error': True}
        self.command.handle(**options)
        
        # Verify all files were attempted
        self.assertEqual(mock_processor.process_file.call_count, 3)
        
        # Verify error was reported
        self.mock_reporter.error.assert_any_call(
            "Error processing file error.md: Invalid markdown syntax"
        )
        
        # Verify URLs and views were generated with the successful files
        mock_processor.generate_urls_and_views.assert_called_once_with(
            [good_file1, good_file2], {}
        )
        
        # Verify success message
        self.mock_reporter.success.assert_any_call(
            "Successfully processed 2 files for test_app"
        )
        
        # Verify warning about failed files
        self.mock_reporter.warning.assert_any_call(
            "Note: 1 files could not be processed: error.md"
        )
        
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_file_exception_without_continue_flag(self, mock_processor_class, mock_setup, 
                                                        mock_find_files, mock_validate, mock_reporter_class):
        """
        Test that processing stops when a file raises an exception and continue_on_error is False.
        This tests the default behavior without the continue flag.
        """
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [
            ('/test/path', 'good.md'),
            ('/test/path', 'error.md'),
            ('/test/path', 'never_processed.md')  # This should never be processed
        ]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        
        # First file succeeds, second file raises exception
        def process_file_side_effect(dirpath, filename, toc):
            if filename == 'error.md':
                raise ValueError("Syntax error in markdown")
            return Mock()  # Return a mock for successful files
        
        mock_processor.process_file.side_effect = process_file_side_effect
        mock_processor_class.return_value = mock_processor
        
        # Execute command without continue_on_error flag (default behavior)
        with self.assertRaises(ProcessingError) as context:
            self.command.handle()
        
        # Verify the error message
        error_msg = str(context.exception)
        self.assertIn("Failed to process file error.md", error_msg)
        self.assertIn("Syntax error in markdown", error_msg)
        
        # Verify only the first two files were attempted (stopped at error)
        self.assertEqual(mock_processor.process_file.call_count, 2)
        
        # Verify error was reported through the reporter
        self.mock_reporter.error.assert_any_call(
            "Error processing file error.md: Syntax error in markdown"
        )
        
        # Verify URLs and views were NOT generated (processing stopped at error)
        mock_processor.generate_urls_and_views.assert_not_called()

    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_url_view_generation_error_detailed(self, mock_processor_class, mock_setup, 
                                            mock_find_files, mock_validate, mock_reporter_class):
        """
        Test detailed error handling when URL and view generation fails.
        This verifies the exact exception and error messages.
        """
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'file1.md'), ('/test/path', 'file2.md')]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        
        # Files process successfully
        processed_file1 = Mock()
        processed_file2 = Mock()
        mock_processor.process_file.side_effect = [processed_file1, processed_file2]
        
        # But URL/view generation fails
        specific_error = ValueError("Duplicate URL pattern detected")
        mock_processor.generate_urls_and_views.side_effect = specific_error
        mock_processor_class.return_value = mock_processor
        
        # Execute command - should raise an OutputGenerationError
        with self.assertRaises(OutputGenerationError) as context:
            self.command.handle()
        
        # Verify error message
        error_msg = str(context.exception)
        self.assertIn("Failed to generate URLs and views", error_msg)
        self.assertIn("Duplicate URL pattern detected", error_msg)
        
        # Verify reporter was called with correct messages
        self.mock_reporter.write.assert_any_call("Generating URLs and views...")
        self.mock_reporter.error.assert_any_call(
            "Error generating URLs and views: Duplicate URL pattern detected"
        )
        
        # Verify processor methods were called correctly
        mock_processor.process_file.assert_has_calls([
            call('/test/path', 'file1.md', {}),
            call('/test/path', 'file2.md', {})
        ])
        mock_processor.generate_urls_and_views.assert_called_once_with(
            [processed_file1, processed_file2], {}
        )

    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_block_discovery_warning_detailed(self, mock_processor_class, mock_setup, mock_find_files,
                                            mock_validate, mock_discover, mock_reporter_class):
        """
        Test detailed handling of warnings during block discovery.
        This verifies that processing continues even when block discovery fails.
        """
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup block discovery error
        mock_discover.side_effect = ImportError("Cannot import module 'custom_blocks'")
        
        # Setup other mocks for successful processing
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        mock_find_files.return_value = [('/test/path', 'file1.md')]
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create processor mock for successful processing
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        mock_processor.process_file.return_value = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Execute command - should complete despite block discovery error
        self.command.handle()
        
        # Verify warning was reported through reporter
        self.mock_reporter.warning.assert_any_call(
            "Error during block discovery: Cannot import module 'custom_blocks'. "
            "Processing will continue but some content may not render correctly."
        )
        
        # Verify processing continued after the warning
        mock_processor.process_file.assert_called_once()
        mock_processor.generate_urls_and_views.assert_called_once()
        
        # Verify success message
        self.mock_reporter.success.assert_any_call(
            "Successfully processed 1 files for test_app"
        )
        
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownReporter')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_find_files_general_exception(self, mock_find_files, mock_validate, mock_reporter_class):
        """
        Test handling of general exceptions during markdown file discovery.
        This verifies that any exception is properly wrapped in a ContentDiscoveryError.
        """
        # Setup reporter mock
        mock_reporter_class.return_value = self.mock_reporter
        
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], [None], [None])
        
        # Simulate a general exception (not ContentDiscoveryError) in find_markdown_files
        # This could be an I/O error, permission error, etc.
        mock_find_files.side_effect = RuntimeError("Failed to access directory")
        
        # Execute command - should raise a ContentDiscoveryError that wraps the original exception
        with self.assertRaises(ContentDiscoveryError) as context:
            self.command.handle()
        
        # Verify that the original exception message is included in the wrapped exception
        error_msg = str(context.exception)
        self.assertIn("Failed to discover markdown files", error_msg)
        self.assertIn("Failed to access directory", error_msg)
        
        # Verify find_markdown_files was called with the correct path
        mock_find_files.assert_called_once_with('/test/path')
        
        # Verify the error messages reported through the reporter
        # The first error is for the pair processing failure
        self.mock_reporter.error.assert_any_call(
            "Error processing pair 1/1: /test/path → test_app: Failed to discover markdown files: Failed to access directory"
        )
        
        # The second error is from the general command failure
        self.mock_reporter.error.assert_any_call(
            "Command failed: Failed to discover markdown files: Failed to access directory"
        )