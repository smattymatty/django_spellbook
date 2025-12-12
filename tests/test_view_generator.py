import unittest
from unittest.mock import patch, Mock, MagicMock
import datetime
from pathlib import Path
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.view_generator import ViewGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext

class TestViewGeneratorRefactored(TestCase):
    """Tests specifically for the refactored ViewGenerator with SpellbookContext delegation."""
    
    def setUp(self):
        """Set up test environment."""
        self.view_generator = ViewGenerator("test_app", "content")
        
        # Create a properly mocked SpellbookContext
        self.mock_context = Mock(spec=SpellbookContext)
        
        # Setup default return values for context methods
        self.mock_context.to_dict.return_value = {
            'title': 'Test Page',
            'created_at': datetime.datetime(2023, 1, 1),
            'updated_at': datetime.datetime(2023, 2, 1),
            'url_path': 'test/page',
            'raw_content': 'Test content',
            'is_public': True,
            'tags': ['test', 'example'],
            'custom_meta': {'key': 'value'}
        }
        
        self.mock_context.prepare_metadata.return_value = {
            'title': 'Test Page',
            'created_at': datetime.datetime(2023, 1, 1),
            'updated_at': datetime.datetime(2023, 2, 1),
            'url_path': 'test/page',
            'raw_content': 'Test content',
            'is_public': True,
            'tags': ['test', 'example'],
            'custom_meta': {'key': 'value'},
            'namespace': 'test_app',
            'url_name': 'test_page',
            'namespaced_url': 'test_app:test_page'
        }
        
        self.mock_context.validate.return_value = []  # No validation errors
        
        # Create a sample processed file
        self.processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=self.mock_context
        )
    
    def test_prepare_context_dict_uses_to_dict(self):
        """Test that _prepare_context_dict correctly uses context.to_dict()."""
        result = self.view_generator._prepare_context_dict(self.mock_context)
        
        # Verify to_dict was called
        self.mock_context.to_dict.assert_called_once()
        
        # Verify the result is what to_dict returned
        self.assertEqual(result, self.mock_context.to_dict.return_value)
    
    def test_prepare_metadata_uses_context_prepare_metadata(self):
        """Test that _prepare_metadata correctly uses context.prepare_metadata()."""
        result = self.view_generator._prepare_metadata(self.processed_file)
        
        # Verify prepare_metadata was called with correct arguments
        self.mock_context.prepare_metadata.assert_called_once_with(
            'test_app', 
            'test/page'
        )
        
        # Verify the result is what prepare_metadata returned
        self.assertEqual(result, self.mock_context.prepare_metadata.return_value)
    
    def test_validate_required_attributes_uses_context_validate(self):
        """Test that validate_required_attributes correctly uses context.validate()."""
        # Call the method - should not raise any exceptions
        self.view_generator.validate_required_attributes(self.processed_file)
        
        # Verify validate was called
        self.mock_context.validate.assert_called_once()
    
    def test_prepare_metadata_with_failing_context_method(self):
        """Test _prepare_metadata when context.prepare_metadata raises an exception."""
        view_generator = ViewGenerator("test_app")
        
        # Create a context class with a prepare_metadata method that raises an exception
        class TestContextWithFailingMethod:
            def prepare_metadata(self, content_app, relative_url):
                raise Exception("Test exception")
            
            def __init__(self):
                self.title = "Fallback Title"
                self.published = datetime.datetime(2023, 1, 1)
                self.modified = datetime.datetime(2023, 2, 1)
                self.raw_content = "Fallback content"
                self.is_public = True
                self.tags = ["fallback", "test"]
                self.custom_meta = {"fallback": "value"}
        
        # Create a processed file with our custom context
        mock_context = TestContextWithFailingMethod()
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Patch logger and get_clean_url
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            with patch('django_spellbook.management.commands.processing.view_generator.get_clean_url', 
                    return_value='test/page'):
                result = view_generator._prepare_metadata(processed_file)
                
                # Verify warning was logged about the failing method
                warning_called = False
                for call in mock_logger.warning.call_args_list:
                    args = call[0]
                    if args and "Error using context.prepare_metadata" in args[0]:
                        warning_called = True
                        break
                
                self.assertTrue(warning_called, "Warning about prepare_metadata error was not logged")
                
                # Verify fallback implementation worked
                self.assertEqual(result['title'], "Fallback Title")
                self.assertEqual(result['is_public'], True)
                self.assertEqual(result['tags'], ["fallback", "test"])
                self.assertIn('namespace', result)
                self.assertEqual(result['namespace'], 'test_app')
    
    def test__prepare_context_dict_success(self):
        """Test _prepare_context_dict with a successful conversion."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample SpellbookContext
        context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content="Test content",
            is_public=True,
            tags=["test", "example"],
            custom_meta={"key": "value"}
        )
        
        result = view_generator._prepare_context_dict(context)
        
        # Verify other keys are converted
        self.assertIn('title', result)
        self.assertIn('published', result)
        self.assertIn('modified', result)
        self.assertIn('url_path', result)
        self.assertIn('raw_content', result)
        self.assertIn('is_public', result)
        self.assertIn('tags', result)
        self.assertIn('custom_meta', result)
    
    def test_validate_required_attributes_with_list_errors(self):
        """Test validation when context.validate returns a list of errors."""
        # Make validate return a list of errors
        self.mock_context.validate.return_value = ["Error 1", "Error 2"]
        
        # Should raise ValueError with joined errors
        with self.assertRaises(ValueError) as context:
            self.view_generator.validate_required_attributes(self.processed_file)
        
        # Check error message
        self.assertIn("Context validation failed: Error 1, Error 2", str(context.exception))
    
    def test_validate_required_attributes_with_non_list_error(self):
        """Test validation when context.validate returns a non-list error."""
        # Make validate return a string
        self.mock_context.validate.return_value = "Single error string"
        
        # Should raise ValueError with the error string
        with self.assertRaises(ValueError) as context:
            self.view_generator.validate_required_attributes(self.processed_file)
        
        # Check error message
        self.assertIn("Context validation failed: Single error string", str(context.exception))
    
    def test_validate_required_attributes_with_exception_in_validate(self):
        """Test validation when context.validate raises an exception."""
        # Make validate raise an exception
        self.mock_context.validate.side_effect = RuntimeError("Unexpected error")
        
        # Patch logger to verify warning
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            # Should NOT raise exception but log warning
            self.view_generator.validate_required_attributes(self.processed_file)
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            self.assertIn("Error during context validation", mock_logger.warning.call_args[0][0])
    
    def test_generate_view_function_delegates_to_context_methods(self):
        """Test _generate_view_function delegates to context methods correctly."""
        # Setup necessary mocks
        with patch('django_spellbook.management.commands.processing.view_generator.generate_view_name', return_value="test_page"):
            with patch('django_spellbook.management.commands.processing.view_generator.get_template_path', return_value="test_app/template.html"):
                with patch('django_spellbook.management.commands.processing.view_generator.get_clean_url', return_value="test/page"):
                    result = self.view_generator._generate_view_function(self.processed_file)
                    
                    # Verify context methods were called
                    self.mock_context.to_dict.assert_called_once()
                    self.mock_context.prepare_metadata.assert_called_once()
                    self.mock_context.validate.assert_called_once()
                    
                    # Verify view function contains expected content
                    self.assertIn("def test_page(request):", result)
                    self.assertIn("return render(request, 'test_app/template.html'", result)
    
    def test_validate_required_attributes_with_value_error_in_validate(self):
        """Test validation when context.validate raises a ValueError."""
        # Make validate raise a ValueError
        self.mock_context.validate.side_effect = ValueError("Custom validation error")
        
        # Should re-raise the ValueError
        with self.assertRaises(ValueError) as context:
            self.view_generator.validate_required_attributes(self.processed_file)
        
        # Check error message
        self.assertEqual(str(context.exception), "Custom validation error")
        
    def test__prepare_toc_success(self):
        """Test _prepare_toc with a successful conversion."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample context dict
        context_dict = {
            'title': 'Test Page',
            'published': datetime.datetime(2023, 1, 1),
            'modified': datetime.datetime(2023, 2, 1),
            'url_path': 'test/page',
            'raw_content': 'Test content',
            'is_public': True,
            'tags': ['test', 'example'],
            'custom_meta': {'key': 'value'},
            'toc': {"dummy": "toc"}
        }
        
        result = view_generator._prepare_toc(context_dict)
        
        # Verify toc is removed
        self.assertIn('toc', result)
        
        # Verify other keys are converted
        self.assertIn('title', result)
        self.assertIn('published', result)
        self.assertIn('modified', result)
        self.assertIn('url_path', result)
        self.assertIn('raw_content', result)
        self.assertIn('is_public', result)
        self.assertIn('tags', result)
        self.assertIn('custom_meta', result)
        
        
class TestViewGeneratorEdgeCases(TestCase):
    def setUp(self):
        """Set up test environment."""
        self.view_generator = ViewGenerator("test_app", "content")
        self.mock_context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content="Test content",
            is_public=True,
            tags=["test", "example"],
            custom_meta={"key": "value"}
        )
    """Tests for edge cases in the ViewGenerator."""
    def test_empty_string_as_content_app(self):
        """Test initialization with empty string as content_app."""
        with self.assertRaises(CommandError) as context:
            ViewGenerator("")
            
    def test_genarate_view_functions_with_empty_list(self):
        """Test generate_view_functions with an empty list."""
        view_generator = ViewGenerator("test_app")
        
        # Test with empty list - should return empty list
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator.generate_view_functions([])
            
            self.assertEqual(result, [])
            mock_logger.warning.assert_called_once()
            self.assertIn("No processed files provided", mock_logger.warning.call_args[0][0])
            
            
    def test_generate_view_functions_with_none(self):
        """Test generate_view_functions with None."""
        view_generator = ViewGenerator("test_app")
        
        # Test with None - should return empty list
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator.generate_view_functions(None)
            
            self.assertEqual(result, [])
            mock_logger.warning.assert_called_once()
            self.assertIn("No processed files provided", mock_logger.warning.call_args[0][0])
            
    def test_generate_view_functions_with_non_processed_file(self):
        """Test generate_view_functions with a non-ProcessedFile object."""
        view_generator = ViewGenerator("test_app")
        
        # Test with None - should return empty list
        with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
            result = view_generator.generate_view_functions([1, 2, 3])
            
            self.assertEqual(result, [])
            mock_logger.warning.assert_called()
            self.assertIn("No view", mock_logger.warning.call_args[0][0])
            
    def test_generate_view_function_where_no_view_name(self):
        """Test _generate_view_function where no view_name is generated."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample processed file
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=self.mock_context
        )
        
        # Mock generate_view_name to return empty string
        with patch('django_spellbook.management.commands.processing.view_generator.generate_view_name', 
                return_value=""):
            # Mock logger to test for errors
            with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                # Should raise CommandError
                with self.assertRaises(CommandError) as context:
                    view_generator._generate_view_function(processed_file)
                
                # Verify the CommandError message contains the expected text
                self.assertIn("Could not generate valid view name", str(context.exception))
                
                # Verify error was logged
                mock_logger.error.assert_called_once()
                self.assertIn("Failed to generate view function", mock_logger.error.call_args[0][0])
        
    def test_context_dictionary_security_validation_fails(self):
        """Test _generate_view_function when context security validation fails."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample processed file
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=self.mock_context
        )
        
        # Mock methods to isolate the security validation part
        with patch('django_spellbook.management.commands.processing.view_generator.generate_view_name', 
                return_value="test_view"):
            with patch('django_spellbook.management.commands.processing.view_generator.get_template_path', 
                    return_value="template/path.html"):
                with patch('django_spellbook.management.commands.processing.view_generator.get_clean_url', 
                        return_value="clean/url"):
                    with patch.object(view_generator, '_prepare_metadata', return_value={}):
                        with patch.object(view_generator, '_prepare_context_dict') as mock_prepare_context:
                            with patch.object(view_generator, 'check_for_dangerous_content', 
                                            side_effect=ValueError("Dangerous content detected")):
                                with patch('django_spellbook.management.commands.processing.view_generator.logger') as mock_logger:
                                    # Set up mock to return something that will trigger the security check
                                    mock_prepare_context.return_value = {"dangerous": "content"}
                                    
                                    # Call the method
                                    result = view_generator._generate_view_function(processed_file)
                                    
                                    # Verify error was logged
                                    mock_logger.error.assert_called_once()
                                    self.assertIn("security validation failed", mock_logger.error.call_args[0][0])
                                    
                                    # Verify empty context is used
                                    self.assertIn("context = {}", result)
                                    
    def test__safe_get_attr_returns_default_when_attr_not_found(self):
        """Test _safe_get_attr when attribute is not found."""
        view_generator = ViewGenerator("test_app")
        
        returned_value = view_generator._safe_get_attr(None, "test", default="default")
        
        self.assertEqual(returned_value, "default")
        
    def test_prepare_metadata_with_no_url_path(self):
        """Test _prepare_metadata when there is no url_path."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample processed file
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('../test/template.html'),
            relative_url='test/page',
            context=self.mock_context
            )
        
        returned_metadata = view_generator._prepare_metadata(processed_file)
        
        self.assertEqual(returned_metadata['title'], 'Error preparing metadata')
        
    def test__prepare_toc_with_non_dict_toc(self):
        """Test _prepare_toc with a non-dict TOC."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample context dict
        context_dict = {
            'title': 'Test Page',
            'created_at': datetime.datetime(2023, 1, 1),
            'updated_at': datetime.datetime(2023, 2, 1),
            'url_path': 'test/page',
            'raw_content': 'Test content',
            'is_public': True,
            'tags': ['test', 'example'],
            'custom_meta': {'key': 'value'},
            'toc': 123  # Non-dict TOC
        }
                
        with self.assertRaises(Exception) as context:
            view_generator._prepare_toc(context_dict)
            
    def test_validate_required_attributes_with_missing_relative_url(self):
        """Test validate_required_attributes with missing relative_url."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample processed file
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='',
            context=self.mock_context
        )
        
        # Should raise ValueError with joined errors
        with self.assertRaises(ValueError) as context:
            view_generator.validate_required_attributes(processed_file)
        
        # Check error message
        self.assertIn("missing relative_url", str(context.exception))
        
    def test_validate_required_attributes_with_missing_context(self):
        """Test validate_required_attributes with missing context."""
        view_generator = ViewGenerator("test_app")
        
        # Create a sample processed file
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=None
        )
        
        # Should raise ValueError with joined errors
        with self.assertRaises(ValueError) as context:
            view_generator.validate_required_attributes(processed_file)

        # Check error message
        self.assertIn("missing context", str(context.exception))


class TestParentDirectoryContext(TestCase):
    """Tests for parent directory context calculation in ViewGenerator."""

    def setUp(self):
        """Set up test environment."""
        self.view_generator = ViewGenerator("test_app", "content")

    def test_calculate_parent_directory_context_with_subdirectory(self):
        """Test parent directory calculation for page in subdirectory."""
        result = self.view_generator._calculate_parent_directory_context('guides/getting-started')

        self.assertEqual(result['url'], 'test_app:test_app_directory_index_guides')
        self.assertEqual(result['name'], 'Guides')

    def test_calculate_parent_directory_context_with_nested_directory(self):
        """Test parent directory calculation for deeply nested page."""
        result = self.view_generator._calculate_parent_directory_context('docs/api/reference')

        self.assertEqual(result['url'], 'test_app:test_app_directory_index_docs_api')
        self.assertEqual(result['name'], 'Api')

    def test_calculate_parent_directory_context_at_root(self):
        """Test parent directory calculation for root-level page."""
        result = self.view_generator._calculate_parent_directory_context('home')

        # Root-level pages should link to root directory index with url_prefix name
        self.assertEqual(result['url'], 'test_app:test_app_directory_index_root_test_app')
        self.assertEqual(result['name'], 'Content')

    def test_calculate_parent_directory_context_with_leading_slash(self):
        """Test parent directory calculation with leading slash."""
        result = self.view_generator._calculate_parent_directory_context('/guides/getting-started/')

        self.assertEqual(result['url'], 'test_app:test_app_directory_index_guides')
        self.assertEqual(result['name'], 'Guides')

    def test_calculate_parent_directory_context_with_underscores(self):
        """Test parent directory humanization with underscores."""
        result = self.view_generator._calculate_parent_directory_context('api_reference/endpoints')

        self.assertEqual(result['url'], 'test_app:test_app_directory_index_api_reference')
        self.assertEqual(result['name'], 'Api Reference')

    def test_calculate_parent_directory_context_with_dashes(self):
        """Test parent directory humanization with dashes."""
        result = self.view_generator._calculate_parent_directory_context('getting-started/quick-guide')

        self.assertEqual(result['url'], 'test_app:test_app_directory_index_getting_started')
        self.assertEqual(result['name'], 'Getting Started')
