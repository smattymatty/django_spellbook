# django_spellbook/tests/test_spellbook_md_command.py

import unittest
from unittest.mock import patch, Mock, call, MagicMock
from pathlib import Path
from io import StringIO
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django_spellbook.management.commands.spellbook_md import Command
from django.core.management import call_command

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
        mock_validate.return_value = (['/test/path'], ['test_app'])
        
        # Execute command
        self.command.handle()
        
        # Verify blocks were discovered
        mock_discover.assert_called_once_with(self.command.stdout)
        
        # Verify settings were validated
        mock_validate.assert_called_once()
        
        # Verify processing was called with correct arguments
        mock_process_pair.assert_called_once_with('/test/path', 'test_app')
        
        # Verify success message was output
        self.command.stdout.write.assert_any_call(
            self.command.style.SUCCESS(
                "Processing source-destination pair 1/1: /test/path → test_app"
            )
        )

    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_multiple_pairs(self, mock_process_pair, mock_validate, mock_discover):
        """Test handling of multiple source-destination pairs"""
        # Set up mocks
        mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'])
        
        # Execute command
        self.command.handle()
        
        # Verify processing was called twice with correct arguments
        expected_calls = [
            call('/path1', 'app1'),
            call('/path2', 'app2')
        ]
        self.assertEqual(mock_process_pair.call_count, 2)
        mock_process_pair.assert_has_calls(expected_calls)
        
        # Verify success messages
        self.command.stdout.write.assert_any_call(
            self.command.style.SUCCESS(
                "Processing source-destination pair 1/2: /path1 → app1"
            )
        )
        self.command.stdout.write.assert_any_call(
            self.command.style.SUCCESS(
                "Processing source-destination pair 2/2: /path2 → app2"
            )
        )

    # In test_handle_error_single_pair
    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_error_single_pair(self, mock_process_pair, mock_validate, mock_discover):
        """Test error handling with a single pair (should raise)"""
        # Set up mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
        
        # Set up error
        test_error = CommandError("Test processing error")
        mock_process_pair.side_effect = test_error
        
        # Execute command - should raise the error
        with self.assertRaises(CommandError) as context:
            self.command.handle()
        
        # Verify it's the same error
        self.assertEqual(str(context.exception), "Test processing error")
        
        # Verify error message was output - check for substring instead of exact match
        error_logged = False
        for call_args in self.command.stdout.write.call_args_list:
            args = call_args[0]
            if len(args) > 0 and isinstance(args[0], str) and "Error processing pair" in args[0] and "Test processing error" in args[0]:
                error_logged = True
                break
        
        self.assertTrue(error_logged, "Error message was not properly logged")


    @patch('django_spellbook.management.commands.spellbook_md.discover_blocks')
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_handle_error_multiple_pairs(self, mock_process_pair, mock_validate, mock_discover):
        """Test error handling with multiple pairs (should continue)"""
        # Set up mocks
        mock_validate.return_value = (['/path1', '/path2', '/path3'], ['app1', 'app2', 'app3'])
        
        # Set up error for the second pair
        def side_effect(path, app):
            if path == '/path2':
                raise CommandError("Test processing error")
            return 1  # Return an integer count on success (not None)
        
        mock_process_pair.side_effect = side_effect
        
        # Execute command
        self.command.handle()
        
        # Verify all pairs were attempted
        expected_calls = [
            call('/path1', 'app1'),
            call('/path2', 'app2'),
            call('/path3', 'app3')
        ]
        self.assertEqual(mock_process_pair.call_count, 3)
        mock_process_pair.assert_has_calls(expected_calls)
        
        # Verify error message and continue message - use substring checks
        error_logged = False
        continue_logged = False
        
        for call_args in self.command.stdout.write.call_args_list:
            args = call_args[0]
            if len(args) > 0 and isinstance(args[0], str):
                if "Error processing pair" in args[0] and "Test processing error" in args[0]:
                    error_logged = True
                elif "Continuing with next pair" in args[0]:
                    continue_logged = True
        
        self.assertTrue(error_logged, "Error message was not logged")
        self.assertTrue(continue_logged, "Continue message was not logged")
    
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_process_pair_no_files(self, mock_find_files):
        """Test error when no markdown files are found"""
        # Set up mock
        mock_find_files.return_value = []
        
        # Execute and test
        with self.assertRaises(CommandError) as context:
            self.command._process_source_destination_pair('/test/path', 'test_app')
        
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
        
        # Execute
        self.command._process_source_destination_pair('/test/path', 'test_app')
        
        # Verify processor was initialized correctly
        mock_processor_class.assert_called_once_with(
            content_app='test_app',
            source_path='/test/path',
            content_dir_path='/content/dir/path',
            template_dir='/template/dir'
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
        self.command.stdout.write.assert_any_call(
            self.command.style.SUCCESS(
                "Successfully processed 2 files for test_app"
            )
        )

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
        
        # Execute and test
        with self.assertRaises(CommandError) as context:
            self.command._process_source_destination_pair('/test/path', 'test_app')
        
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
        
        # Execute
        self.command._process_source_destination_pair('/test/path', 'test_app')
        
        # Verify all files were attempted
        self.assertEqual(mock_processor.process_file.call_count, 3)
        
        # Verify URLs and views were generated with only the successful file
        mock_processor.generate_urls_and_views.assert_called_once_with(
            [mock_processed_file], 
            {'toc': 'data'}
        )
        
        # Verify success message includes correct count
        self.command.stdout.write.assert_any_call(
            self.command.style.SUCCESS(
                "Successfully processed 1 files for test_app"
            )
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
        
        # Verify error message was output - check for substring instead of exact match
        error_logged = False
        for call_args in self.command.stdout.write.call_args_list:
            args = call_args[0]
            if len(args) > 0 and isinstance(args[0], str) and "Command failed" in args[0] and "Invalid settings" in args[0]:
                error_logged = True
                break
        
        self.assertTrue(error_logged, "Command failed message was not properly logged")
            
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
        self.command.stdout = Mock()
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    def test_configuration_error(self, mock_validate):
        """Test error handling for configuration errors"""
        # Simulate a configuration error
        mock_validate.side_effect = Exception("Missing required settings")
        
        # Execute command - should raise the error
        with self.assertRaises(ConfigurationError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("Settings validation failed", str(context.exception))
        
        # Verify advice was logged
        advice_message_found = False
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "check your Django settings.py" in args[0]:
                advice_message_found = True
                break
        
        self.assertTrue(advice_message_found, "Advice message was not logged")
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_content_discovery_error_no_files(self, mock_find_files, mock_validate):
        """Test error handling when no markdown files are found"""
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
        mock_find_files.return_value = []
        
        # Execute command - should raise the error
        with self.assertRaises(ContentDiscoveryError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("No markdown files found", str(context.exception))
        
        # Verify advice was logged
        advice_message_found = False
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "Make sure the directory exists" in args[0]:
                advice_message_found = True
                break
        
        self.assertTrue(advice_message_found, "Advice message was not logged")
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    def test_content_discovery_error_exception(self, mock_find_files, mock_validate):
        """Test error handling when file discovery throws an exception"""
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
        mock_find_files.side_effect = OSError("Permission denied")
        
        # Execute command - should raise the error
        with self.assertRaises(ContentDiscoveryError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("Failed to discover markdown files", str(context.exception))
        self.assertIn("Permission denied", str(context.exception))
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    def test_configuration_error_directory_setup(self, mock_setup, mock_find_files, mock_validate):
        """Test error handling for directory setup failures"""
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
        mock_find_files.return_value = [('/test/path', 'test.md')]
        mock_setup.side_effect = OSError("Permission denied")
        
        # Execute command - should raise the error
        with self.assertRaises(ConfigurationError) as context:
            self.command.handle()
        
        # Verify error message
        self.assertIn("Failed to set up directory structure", str(context.exception))
        self.assertIn("Permission denied", str(context.exception))
        
        # Verify advice was logged
        advice_message_found = False
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "Check that the content app exists" in args[0]:
                advice_message_found = True
                break
        
        self.assertTrue(advice_message_found, "Advice message was not logged")
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_toc_error_continues_processing(self, mock_processor_class, mock_setup, mock_find_files, mock_validate):
        """Test error handling for TOC building failures"""
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
        mock_find_files.return_value = [('/test/path', 'test.md')]
        mock_setup.return_value = ('/test/path/app', '/test/path/app/templates')
        
        # Create a mock processor with a failing build_toc method
        mock_processor = Mock()
        mock_processor.build_toc.side_effect = Exception("TOC error")
        mock_processor.process_file.return_value = Mock()  # Process succeeds
        mock_processor_class.return_value = mock_processor
        
        # Execute command
        self.command.handle()
        
        # Verify warning was logged
        warning_message_found = False
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "Error building table of contents" in args[0]:
                warning_message_found = True
                break
        
        self.assertTrue(warning_message_found, "Warning about TOC failure was not logged")
        
        # Verify the command continued with an empty TOC
        mock_processor.process_file.assert_called_once()
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_process_multiple_pairs_summary(self, mock_processor_class, mock_setup, mock_find_files, mock_validate):
        """Test summary report with multiple source-destination pairs"""
        # Setup mocks
        mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'])
        
        # Mock file discovery for each pair
        mock_find_files.side_effect = [
            [('/path1', 'file1.md')],  # First pair has files
            []  # Second pair has no files (will fail)
        ]
        
        mock_setup.return_value = ('/content/path', '/template/path')
        
        # Create a successful processor for first pair
        mock_processor = Mock()
        mock_processor.build_toc.return_value = {}
        mock_processor.process_file.return_value = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Execute command - second pair will fail but command should continue
        self.command.handle()
        
        # Verify summary was generated
        summary_message_found = False
        failed_pair_message_found = False
        
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "Processing Summary:" in args[0]:
                summary_message_found = True
            elif isinstance(args[0], str) and "1 of 2 pairs processed successfully" in args[0]:
                failed_pair_message_found = True
        
        self.assertTrue(summary_message_found, "Summary was not generated")
        self.assertTrue(failed_pair_message_found, "Failed pair message not found in summary")
    
    @patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings')
    @patch('django_spellbook.management.commands.spellbook_md.find_markdown_files')
    @patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor')
    def test_continue_on_error_flag(self, mock_processor_class, mock_setup, mock_find_files, mock_validate):
        """Test --continue-on-error flag allows processing to continue after file errors"""
        # Setup mocks
        mock_validate.return_value = (['/test/path'], ['test_app'])
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
        # This is critical - we need to pass it as an option rather than setting the attribute
        options = {'continue_on_error': True}
        self.command.handle(**options)
        
        # Verify both files were attempted
        self.assertEqual(mock_processor.process_file.call_count, 2)
        
        # Verify URLs and views were generated with the successful file
        mock_processor.generate_urls_and_views.assert_called_once()
        
        # Verify error was logged but processing continued
        error_logged = False
        success_logged = False
        
        for call_args in self.command.stdout.write.call_args_list:
            args = call_args[0]
            if len(args) > 0 and isinstance(args[0], str):
                if "Error processing file" in args[0]:
                    error_logged = True
                elif "Successfully processed" in args[0] and "1 files" in args[0]:
                    success_logged = True
        
        self.assertTrue(error_logged, "Error message was not logged")
        self.assertTrue(success_logged, "Success message was not logged")
        
    def test_block_discovery_error(self):
        """Test handling of errors during block discovery."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.discover_blocks') as mock_discover, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'])
            mock_discover.side_effect = Exception("Test discovery error")
            mock_find_files.return_value = [('/test/path', 'test.md')]
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Setup processor mock
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            mock_processor.process_file.return_value = MagicMock()
            mock_processor_class.return_value = mock_processor
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn('Error during block discovery: Test discovery error', output)
            self.assertIn('Processing will continue but some content may not render correctly', output)
            
            # Verify command continued processing
            self.assertIn('Successfully processed 1 files for test_app', output)

    def test_processor_initialization_error(self):
        """Test handling of errors during processor initialization."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'])
            mock_find_files.return_value = [('/test/path', 'test.md')]
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Make processor initialization fail
            mock_processor_class.side_effect = Exception("Test processor initialization error")
            
            # Run the command - should raise a ProcessingError
            out = StringIO()
            with self.assertRaises(ProcessingError) as context:
                call_command('spellbook_md', stdout=out)
            
            # Check the exception message
            self.assertIn('Failed to initialize markdown processor', str(context.exception))
            self.assertIn('Test processor initialization error', str(context.exception))

    def test_url_view_generation_error(self):
        """Test handling of errors during URL and view generation."""
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
            mock_processor.process_file.return_value = MagicMock()
            
            # Make URL/view generation fail
            mock_processor.generate_urls_and_views.side_effect = Exception("Test URL generation error")
            mock_processor_class.return_value = mock_processor
            
            # Run the command - should raise an OutputGenerationError
            out = StringIO()
            with self.assertRaises(OutputGenerationError) as context:
                call_command('spellbook_md', stdout=out)
            
            # Check the exception message
            self.assertIn('Failed to generate URLs and views', str(context.exception))
            self.assertIn('Test URL generation error', str(context.exception))
            
            # Check output
            output = out.getvalue()
            self.assertIn('Error generating URLs and views', output)
            
    def test_error_stops_processing_by_default(self):
        """Test that errors stop processing by default without continue_on_error flag."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
            patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
            patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
            patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'])
            mock_find_files.return_value = [
                ('/test/path', 'good.md'),
                ('/test/path', 'bad.md'),
                ('/test/path', 'never_processed.md')  # This file should never be processed
            ]
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Setup processor mock
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            
            # Configure process_file to succeed for good.md but fail for bad.md
            def process_file_side_effect(dirpath, filename, toc):
                if filename == 'bad.md':
                    raise Exception("Test error in file processing")
                return MagicMock()  # Return a mock for successful file
            
            mock_processor.process_file.side_effect = process_file_side_effect
            mock_processor_class.return_value = mock_processor
            
            # Run the command WITHOUT continue-on-error flag (default behavior)
            out = StringIO()
            
            # It should raise a ProcessingError
            with self.assertRaises(ProcessingError) as context:
                call_command('spellbook_md', stdout=out)
            
            # Check the exception message
            self.assertIn('Failed to process file bad.md', str(context.exception))
            self.assertIn('Test error in file processing', str(context.exception))
            
            # Verify only the first file was processed before the error
            self.assertEqual(mock_processor.process_file.call_count, 2)  # only good.md and bad.md were attempted
            
            # Check output
            output = out.getvalue()
            self.assertIn('Error processing file bad.md', output)
            
            # generate_urls_and_views should not have been called since processing stopped at the error
            mock_processor.generate_urls_and_views.assert_not_called()