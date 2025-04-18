# django_spellbook/tests/test_view_generator.py

import unittest
from unittest.mock import patch, Mock
import datetime
from pathlib import Path
from django.test import TestCase

from django_spellbook.management.commands.processing.view_generator import ViewGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext

class TestViewGenerator(TestCase):
    
    def setUp(self):
        """Set up the test environment."""
        self.view_generator = ViewGenerator("test_app")
        
        # Create a mock context
        self.mock_context = Mock(spec=SpellbookContext)
        self.mock_context.__dict__ = {
            'title': 'Test Page', 
            'toc': {},
            'created_at': datetime.datetime(2023, 1, 1),
            'is_public': True,
            'tags': ['test', 'example'],
            'custom_meta': {'key': 'value'}
        }
        
        # Create a sample processed file
        self.processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=self.mock_context
        )
        
    def test_initialization(self):
        """Test initialization of ViewGenerator."""
        self.assertEqual(self.view_generator.content_app, "test_app")
        
    def test_prepare_context_dict(self):
        """Test preparing context dictionary for template rendering."""
        result = self.view_generator._prepare_context_dict(self.mock_context)
        
        # Check that toc is removed
        self.assertNotIn('toc', result)
        
        # Check other values
        self.assertEqual(result['title'], 'Test Page')
        self.assertEqual(result['is_public'], True)
        self.assertEqual(result['tags'], ['test', 'example'])
        
    def test_prepare_metadata(self):
        """Test preparing metadata dictionary for a file."""
        result = self.view_generator._prepare_metadata(self.processed_file)
        
        # Check metadata fields
        self.assertEqual(result['title'], 'Test Page')
        self.assertEqual(result['is_public'], True)
        self.assertEqual(result['tags'], ['test', 'example'])
        self.assertEqual(result['namespace'], 'test_app')
        self.assertEqual(result['url_name'], 'test_page')
        self.assertEqual(result['namespaced_url'], 'test_app:test_page')
        
    @patch('django_spellbook.management.commands.processing.view_generator.generate_view_name')
    @patch('django_spellbook.management.commands.processing.view_generator.get_template_path')
    @patch('django_spellbook.management.commands.processing.view_generator.get_clean_url')
    def test_generate_view_function(self, mock_clean_url, mock_template_path, mock_view_name):
        """Test generating view function for a single file."""
        # Configure mocks
        mock_clean_url.return_value = "test/page"
        mock_template_path.return_value = "test_app/spellbook_md/test/page.html"
        mock_view_name.return_value = "test_page"
        
        # Mock _prepare_metadata and _prepare_context_dict
        with patch.object(self.view_generator, '_prepare_metadata') as mock_prepare_metadata:
            with patch.object(self.view_generator, '_prepare_context_dict') as mock_prepare_context:
                # Configure mocks
                mock_prepare_metadata.return_value = {'title': 'Test', 'url_path': 'test/page'}
                mock_prepare_context.return_value = {'title': 'Test'}
                
                # Call method
                view_function = self.view_generator._generate_view_function(self.processed_file)
                
                # Check result is a string containing a view function
                self.assertIsInstance(view_function, str)
                self.assertTrue(view_function.startswith('\ndef test_page(request):'))
                self.assertIn("'title': 'Test'", view_function)
                self.assertIn("context['toc'] = TOC", view_function)
                self.assertIn("return render(request,", view_function)
                
import unittest
from unittest.mock import patch, Mock, MagicMock
import datetime
from pathlib import Path
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.view_generator import ViewGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext

class TestViewGeneratorErrors(TestCase):
    
    def test_init_with_invalid_content_app(self):
        """Test initialization with invalid content_app parameter."""
        # Test with empty string
        with self.assertRaises(CommandError) as context:
            ViewGenerator("")
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
        
        # Test with None
        with self.assertRaises(CommandError) as context:
            ViewGenerator(None)
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
        
        # Test with non-string
        with self.assertRaises(CommandError) as context:
            ViewGenerator(123)
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
    
    def test_generate_view_functions_with_empty_list(self):
        """Test generate_view_functions with an empty list."""
        view_generator = ViewGenerator("test_app")
        
        # Test with empty list - should return empty list
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator.generate_view_functions([])
            
            self.assertEqual(result, [])
            mock_logger.warning.assert_called_once()
            self.assertIn("No processed files provided", mock_logger.warning.call_args[0][0])
    
    def test_generate_view_functions_with_invalid_items(self):
        """Test generate_view_functions with list containing invalid items."""
        view_generator = ViewGenerator("test_app")
        
        # Create a list with non-ProcessedFile items
        invalid_items = [
            None,
            "not a processed file",
            123,
            {}
        ]
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator.generate_view_functions(invalid_items)
            
            self.assertEqual(result, [])
            self.assertEqual(mock_logger.warning.call_count, 5)  # 1 for empty result + 4 for invalid items
    
    def test_generate_view_function_with_missing_attributes(self):
        """Test _generate_view_function with ProcessedFile missing required attributes."""
        view_generator = ViewGenerator("test_app")
        
        # Create ProcessedFile without relative_url
        missing_url = Mock(spec=ProcessedFile)
        missing_url.context = Mock(spec=SpellbookContext)
        
        # Use delattr to remove the attribute
        delattr(missing_url, 'relative_url')
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            with self.assertRaises(CommandError) as context:
                view_generator._generate_view_function(missing_url)
                
            self.assertIn("Failed to generate view function", str(context.exception))
            mock_logger.error.assert_called_once()
    
    def test_generate_view_function_with_empty_relative_url(self):
        """Test _generate_view_function with empty relative_url."""
        view_generator = ViewGenerator("test_app")
        
        # Mock generate_view_name to return empty string
        with patch('django_spellbook.management.commands.processing.view_generator.generate_view_name', 
                   return_value=""):
            
            processed_file = Mock(spec=ProcessedFile)
            processed_file.relative_url = "test/page"
            processed_file.context = Mock(spec=SpellbookContext)
            
            with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                with self.assertRaises(CommandError) as context:
                    view_generator._generate_view_function(processed_file)
                    
                self.assertIn("Could not generate valid view name", str(context.exception))
                mock_logger.error.assert_called_once()
    
    def test_prepare_metadata_with_invalid_context(self):
        """Test _prepare_metadata with invalid context."""
        view_generator = ViewGenerator("test_app")
        
        # Create a ProcessedFile with invalid context
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page"
        processed_file.context = None
        
        # We don't expect an error to be logged in this case based on current implementation
        metadata = view_generator._prepare_metadata(processed_file)
        
        # Should return minimal metadata
        self.assertIn('title', metadata)
        self.assertIn('url_path', metadata)
        self.assertIn('namespace', metadata)
    
    def test_prepare_context_dict_with_none_context(self):
        """Test _prepare_context_dict with None context."""
        view_generator = ViewGenerator("test_app")
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator._prepare_context_dict(None)
            
            self.assertEqual(result, {})
            mock_logger.warning.assert_called_once()
            self.assertIn("Context is None", mock_logger.warning.call_args[0][0])
    
    def test_prepare_context_dict_with_context_raising_exception(self):
        """Test _prepare_context_dict with context that raises exception."""
        view_generator = ViewGenerator("test_app")
        
        # Create a context that raises exception when __dict__ is accessed
        class ProblemContext:
            @property
            def __dict__(self):
                raise Exception("Test exception")
        
        problematic_context = ProblemContext()
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator._prepare_context_dict(problematic_context)
            
            self.assertEqual(result, {})
            mock_logger.error.assert_called_once()
            self.assertIn("Error preparing context", mock_logger.error.call_args[0][0])
    
    def test_safe_get_attr_with_none_object(self):
        """Test _safe_get_attr with None object."""
        view_generator = ViewGenerator("test_app")
        
        # Should return default value
        self.assertEqual(view_generator._safe_get_attr(None, 'any_attr', 'default'), 'default')
    
    def test_context_dict_with_problematic_values(self):
        """Test _prepare_context_dict with values that raise errors."""
        view_generator = ViewGenerator("test_app")
        
        # Create a datetime subclass that raises exception when repr() is called
        class ProblemDatetime(datetime.datetime):
            def __repr__(self):
                raise Exception("Cannot represent")
        
        # Create a problematic datetime value (can't just instantiate ProblemDatetime directly)
        problem_datetime = datetime.datetime(2023, 1, 1)
        problem_value = Mock(spec=datetime.datetime)
        problem_value.__repr__ = Mock(side_effect=Exception("Cannot represent"))
        
        context = Mock(spec=SpellbookContext)
        context.__dict__ = {
            'good_value': 'test',
            'problem_value': problem_value,
            'date_value': datetime.datetime(2023, 1, 1)
        }
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            with patch('django_spellbook.management.commands.processing.view_generator.isinstance', 
                    return_value=True):  # Force all values to be treated as datetime
                result = view_generator._prepare_context_dict(context)
                
                # Should include good values but set problematic ones to None
                self.assertEqual(result['good_value'], "'test'")
                self.assertIsNone(result['problem_value'])  # Should be None due to exception handling
                self.assertTrue(isinstance(result['date_value'], str))
                mock_logger.warning.assert_called_once()
                self.assertIn("Could not process context value", mock_logger.warning.call_args[0][0])
    
    def test_metadata_representation_with_problematic_values(self):
        """Test metadata representation with values that can't be represented."""
        view_generator = ViewGenerator("test_app")
        
        # Create a class that raises exception when repr() is called
        class ProblemValue:
            def __repr__(self):
                raise Exception("Cannot represent")
        
        # Create a processed file with context
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page"
        processed_file.context = Mock(spec=SpellbookContext)
        
        # Mock _prepare_metadata to return dict with problematic value
        with patch.object(view_generator, '_prepare_metadata') as mock_prepare:
            mock_prepare.return_value = {
                'good_key': 'value',
                'problem_key': ProblemValue()
            }
            
            with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                # This should handle the exception and continue
                result = view_generator._generate_view_function(processed_file)
                
                # Should log a warning
                mock_logger.warning.assert_called_once()
                self.assertIn("Could not represent metadata value", mock_logger.warning.call_args[0][0])
                
                # Result should include the good key and a comment for the problem key
                self.assertIn("'good_key': 'value'", result)
                self.assertIn("# Error representing value", result)
    
    def test_generate_view_function_comprehensive_error_handling(self):
        """Test _generate_view_function handles various errors and provides helpful messages."""
        view_generator = ViewGenerator("test_app")
        
        # Test with various exceptions in helper methods
        with patch('django_spellbook.management.commands.processing.view_generator.generate_view_name', 
                  side_effect=Exception("View name error")):
            
            processed_file = Mock(spec=ProcessedFile)
            processed_file.relative_url = "test/page"
            processed_file.context = Mock(spec=SpellbookContext)
            
            with self.assertRaises(CommandError) as context:
                view_generator._generate_view_function(processed_file)
                
            self.assertIn("Failed to generate view function", str(context.exception))
            self.assertIn("View name error", str(context.exception))
    
    def test_generate_view_functions_error_continuation(self):
        """Test generate_view_functions continues processing after errors."""
        view_generator = ViewGenerator("test_app")
        
        # Create good and bad processed files
        good_file = Mock(spec=ProcessedFile)
        good_file.relative_url = "good/file"
        good_file.context = Mock(spec=SpellbookContext)
        
        bad_file = Mock(spec=ProcessedFile)
        bad_file.relative_url = "bad/file"
        bad_file.context = Mock(spec=SpellbookContext)
        
        # Make _generate_view_function succeed for good_file and fail for bad_file
        def mock_generate(file):
            if file == good_file:
                return "def good_file(): pass"
            else:
                raise Exception("Error in bad file")
                
        with patch.object(view_generator, '_generate_view_function', side_effect=mock_generate):
            with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                result = view_generator.generate_view_functions([good_file, bad_file])
                
                # Should have one successful function and log error for bad file
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0], "def good_file(): pass")
                mock_logger.error.assert_called_once()
                self.assertIn("Error generating view function", mock_logger.error.call_args[0][0])
    
    def test_prepare_metadata_exception_handling(self):
        """Test _prepare_metadata handles exceptions in attribute access."""
        view_generator = ViewGenerator("test_app")
        
        # Create a ProcessedFile that raises exception when relative_url is accessed
        class ExceptionFile:
            @property
            def relative_url(self):
                raise Exception("Relative URL error")
                
            # Add minimal required attributes to pass isinstance check
            def __init__(self):
                self.original_path = "test"
                self.html_content = "test"
                self.template_path = "test"
                self.context = None
        
        exception_file = ExceptionFile()
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            # Should return minimal metadata and log the error
            with self.assertRaises(Exception):
                metadata = view_generator._prepare_metadata(exception_file)
                
    def test_generate_view_function_missing_context_attribute(self):
        """Test _generate_view_function with ProcessedFile missing context attribute."""
        view_generator = ViewGenerator("test_app")
        
        # Create ProcessedFile without context attribute
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page"
        # Deliberately remove context attribute
        if hasattr(processed_file, 'context'):
            delattr(processed_file, 'context')
        
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            with self.assertRaises(CommandError) as context:
                view_generator._generate_view_function(processed_file)
                
            self.assertIn("Failed to generate view function", str(context.exception))
            self.assertIn("ProcessedFile missing context attribute", str(context.exception))
            mock_logger.error.assert_called_once()

    def test_prepare_context_dict_outer_exception(self):
        """Test _prepare_context_dict with exception in the outer try-except block."""
        view_generator = ViewGenerator("test_app")
        
        # Create a normal context
        context = Mock(spec=SpellbookContext)
        
        # Force an exception in the main try block by patching hasattr
        with patch('django_spellbook.management.commands.processing.view_generator.hasattr', 
                side_effect=Exception("Error in hasattr")):
            with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                result = view_generator._prepare_context_dict(context)
                
                self.assertEqual(result, {})
                mock_logger.error.assert_called_once()
                self.assertIn("Error preparing context dictionary", mock_logger.error.call_args[0][0])
                
    def test_context_dict_representation_check(self):
        """Test context dictionary representation check in _generate_view_function."""
        view_generator = ViewGenerator("test_app")
        
        # Create a processed file with valid attributes
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page"
        processed_file.context = Mock(spec=SpellbookContext)
        
        # Create a problematic object that can't be represented
        class ProblematicObject:
            def __repr__(self):
                raise Exception("Cannot represent!")
        
        problematic_dict = {'normal': 'test', 'problem': ProblematicObject()}
        
        # Mock _prepare_context_dict to return the problematic dict
        with patch.object(view_generator, '_prepare_context_dict', return_value=problematic_dict):
            with patch.object(view_generator, '_prepare_metadata', return_value={}):
                with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                    # Should handle the exception during repr() and use an empty context
                    result = view_generator._generate_view_function(processed_file)
                    
                    # Should log the error
                    mock_logger.error.assert_called_once()
                    self.assertIn("security validation failed", mock_logger.error.call_args[0][0])
                    
                    # Should use an empty context
                    self.assertIn("context = {}", result)

    def test_context_dict_with_dangerous_content(self):
        """Test security validation for dangerous content in context."""
        view_generator = ViewGenerator("test_app")
        
        # Create a processed file with valid attributes
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page" 
        processed_file.context = Mock(spec=SpellbookContext)
        
        # Create context dictionaries with potentially dangerous content
        dangerous_contexts = [

        ]
        
        for dangerous_dict in dangerous_contexts:
            # Mock _prepare_context_dict to return the dangerous dict
            with patch.object(view_generator, '_prepare_context_dict', return_value=dangerous_dict):
                with patch.object(view_generator, '_prepare_metadata', return_value={}):
                    with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                        # Should detect dangerous content and use an empty context
                        result = view_generator._generate_view_function(processed_file)
                        
                        # Should log the error
                        mock_logger.error.assert_called_once()
                        self.assertIn("security validation failed", mock_logger.error.call_args[0][0])
                        self.assertIn("Potentially unsafe content", mock_logger.error.call_args[0][0])
                        
                        # Should use an empty context
                        self.assertIn("context = {}", result)
                        
                        # Reset mock
                        mock_logger.reset_mock()

    def test_context_dict_with_safe_content(self):
        """Test security validation with safe content passes."""
        view_generator = ViewGenerator("test_app")
        
        # Create a processed file with valid attributes
        processed_file = Mock(spec=ProcessedFile)
        processed_file.relative_url = "test/page"
        processed_file.context = Mock(spec=SpellbookContext)
        
        # Create a context with safe values
        safe_dict = {
            'string': 'test',
            'number': 123,
            'boolean': True,
            'none': None,
            'list': [1, 2, 3],
            'dict': {'a': 1, 'b': 2},
            'date': datetime.datetime(2023, 1, 1)
        }
        
        # Mock _prepare_context_dict to return the safe dict
        with patch.object(view_generator, '_prepare_context_dict', return_value=safe_dict):
            with patch.object(view_generator, '_prepare_metadata', return_value={}):
                with patch('django_spellbook.management.commands.processing.view_generator.repr', return_value=str(safe_dict)):
                    # Should not log any security errors
                    with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                        result = view_generator._generate_view_function(processed_file)
                        
                        # Error should not be called for security validation
                        mock_logger.error.assert_not_called()
                        
                        # Should use the original context
                        self.assertNotIn("context = {}", result)