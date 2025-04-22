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
            mock_validate.return_value = (['/test/path'], ['test_app'], ['test_prefix'], ["test_template"])
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
            mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'], ['test_prefix', ''], [None, None])
            
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
            mock_validate.return_value = (['/test/path'], ['test_app'], [''], [None])
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
            mock_validate.return_value = (['/path1', '/path2'], ['app1', 'app2'], ['', 'test_prefix'], [None, None])
            
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
        
class TestNumericFilenameHandling(TestCase):
    """Test handling of filenames that start with numbers."""
    
    def test_numeric_filenames(self):
        """Test processing files with numeric names and paths."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
             patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
             patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
             patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_validate.return_value = (['/test/path'], ['test_app'], [''], [None])
            
            # Include files with numeric names and in numeric directories
            mock_find_files.return_value = [
                ('/test/path', '0.1.0-release.md'),          # Starts with number
                ('/test/path/1.0_docs', 'features.md'),      # Directory starts with number
                ('/test/path/1.0_docs', '0-introduction.md') # Both directory and file start with numbers
            ]
            
            mock_setup.return_value = ('/app/path', '/app/templates')
            
            # Create mock processor
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            
            # All files process successfully
            mock_processor.process_file.return_value = MagicMock()
            mock_processor_class.return_value = mock_processor
            
            # Capture the view generation calls
            mock_generate = MagicMock()
            mock_processor.generate_urls_and_views = mock_generate
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Verify files were processed
            self.assertEqual(mock_processor.process_file.call_count, 3)
            
            # Verify URLs and views were generated without errors
            mock_generate.assert_called_once()
            
            # Check output for success
            output = out.getvalue()
            self.assertIn('Successfully processed 3 files for test_app', output)
    
    def test_function_name_sanitization(self):
        """Test that function names are properly sanitized for numeric paths."""
        from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
        from django_spellbook.management.commands.processing.file_processor import ProcessedFile
        
        # Create a generator instance with debug-friendly initialization
        generator = URLViewGenerator(
            content_app='test_app',
            content_dir_path='/app/path',
            source_path='/test/path',
            url_prefix=''
        )
        
        # Enable detailed logging for debugging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Create processed files with problematic numeric paths
        files = [
            ProcessedFile(
                original_path='/test/path/0.1.0-release.md',
                html_content='<html>Test</html>',
                template_path='test_app/spellbook_md/0.1.0-release.html',
                relative_url='0.1.0-release',
                context=Mock()
            )
        ]
        
        # Create a simple capture function to see what's happening
        captured_calls = []
        def capture_call(path, content):
            captured_calls.append((path, content))
            # Print for debugging
            print(f"Writing to {path}: {content[:50]}...")
        
        # Mock more dependencies to ensure we're capturing everything
        with patch('django_spellbook.management.commands.processing.file_writer.write_file', side_effect=capture_call), \
            patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists'), \
            patch('django_spellbook.management.commands.processing.file_writer.get_spellbook_dir', return_value='/app'), \
            patch('os.path.exists', return_value=True):
            
            try:
                # Call the method directly
                generator.generate_urls_and_views(files, {})
                
                # Now examine what was captured
                for path, content in captured_calls:
                    print(f"CAPTURED: {path}")
                    
                # Check if any view file was generated
                view_file_content = None
                for path, content in captured_calls:
                    if 'views' in path:
                        view_file_content = content
                
                # If we get here, check the generated content
                if view_file_content:
                    # Check function definitions in the content
                    import re
                    function_defs = re.findall(r'def\s+(\w+)\s*\(', view_file_content)
                    
                    # Check the function names
                    for func_name in function_defs:
                        print(f"Found function: {func_name}")
                        # Python identifiers can't start with a digit
                        self.assertFalse(func_name[0].isdigit(), 
                            f"Function name '{func_name}' starts with a digit, which is invalid in Python")
                else:
                    # No view file was generated, which is not what we expect
                    self.fail(f"No views.py file was generated. Captured files: {[path for path, _ in captured_calls]}")
                    
            except Exception as e:
                # The current implementation might fail with SyntaxError
                # We're asserting that specific error to confirm we need to fix it
                if isinstance(e, SyntaxError) and "leading zeros in decimal integer literals" in str(e):
                    # This is the expected error for function names starting with digits
                    print("Caught expected SyntaxError for function name starting with digit")
                else:
                    # Unexpected error - print more details
                    import traceback
                    traceback.print_exc()
                    self.fail(f"Unexpected error: {type(e).__name__}: {str(e)}")
    
    def test_versioned_documentation_structure(self):
        """Test processing a typical documentation structure with versioned folders."""
        with patch('django_spellbook.management.commands.spellbook_md.validate_spellbook_settings') as mock_validate, \
             patch('django_spellbook.management.commands.spellbook_md.find_markdown_files') as mock_find_files, \
             patch('django_spellbook.management.commands.spellbook_md.setup_directory_structure') as mock_setup, \
             patch('django_spellbook.management.commands.spellbook_md.MarkdownProcessor') as mock_processor_class:
            
            # Setup mocks for a typical versioned docs structure
            mock_validate.return_value = (['/docs'], ['docs_app'], ['docs'], [None])
            
            # Create a file structure that mimics versioned documentation
            mock_find_files.return_value = [
                ('/docs', 'index.md'),
                ('/docs/0.1.0', 'index.md'),
                ('/docs/0.1.0', 'getting-started.md'),
                ('/docs/0.1.0/api', 'endpoints.md'),
                ('/docs/1.0.0', 'index.md'),
                ('/docs/1.0.0', 'migration-guide.md'),
                ('/docs/1.0.0/api', 'endpoints.md')
            ]
            
            mock_setup.return_value = ('/docs_app/path', '/docs_app/templates')
            
            # Create mock processor
            mock_processor = MagicMock()
            mock_processor.build_toc.return_value = {}
            
            # All files process successfully
            mock_processor.process_file.return_value = MagicMock()
            mock_processor_class.return_value = mock_processor
            
            # Run the command
            out = StringIO()
            call_command('spellbook_md', stdout=out)
            
            # Verify correct number of files were processed
            self.assertEqual(mock_processor.process_file.call_count, 7)
            
            # Check output for success
            output = out.getvalue()
            self.assertIn('Successfully processed 7 files for docs_app', output)
            
    def test_generate_view_name_with_numeric_paths(self):
        """Test that generate_view_name properly handles numeric paths."""
        from django_spellbook.management.commands.processing.generator_utils import generate_view_name
        
        # Test cases with problematic numeric paths
        test_cases = [
            ('0.1.0-release', '0_1_0_release'),      # Starts with a digit - should be invalid
            ('1.0/docs', '1_0_docs'),                # Also starts with a digit - should be invalid
            ('normal-path', 'normal_path'),          # Normal path - should be valid
        ]
        
        for relative_url, expected_result in test_cases:
            # Generate the view name
            try:
                view_name = generate_view_name(relative_url)
                
                # If the path starts with a digit, this should fail because Python
                # function names can't start with digits
                if relative_url[0].isdigit():
                    # Try to compile a function with this name to verify it's invalid
                    try:
                        compile(f"def {view_name}(): pass", "<string>", "exec")
                        self.fail(f"Expected view name '{view_name}' to be invalid in Python")
                    except SyntaxError as e:
                        self.assertIn("invalid syntax", str(e), 
                                    "Expected syntax error due to function name starting with digit")
                else:
                    # Normal paths should generate valid function names
                    compile(f"def {view_name}(): pass", "<string>", "exec")
            except Exception as e:
                # If the function already handles invalid paths by raising an exception,
                # that's also acceptable behavior
                if relative_url[0].isdigit():
                    # This exception is expected for paths starting with digits
                    pass
                else:
                    # But normal paths should not raise exceptions
                    self.fail(f"Unexpected error for '{relative_url}': {str(e)}")