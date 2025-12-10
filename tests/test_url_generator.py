# django_spellbook/tests/test_url_generator.py

import unittest
from unittest.mock import patch, Mock
from pathlib import Path
from django.test import TestCase

from django_spellbook.management.commands.processing.url_generator import URLGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext

class TestURLGenerator(TestCase):
    # TODO: BUG: whenever you have two apps properly configured but no URL_PREFIX set,
    # the urls generated are incorrect, it ignores the first app only only includes the second
    def setUp(self):
        """Set up the test environment."""
        self.url_generator = URLGenerator("test_app")
        
        # Create a mock context
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
        """Test initialization of URLGenerator."""
        self.assertEqual(self.url_generator.content_app, "test_app")
        
    @patch('django_spellbook.management.commands.processing.url_generator.generate_view_name')
    @patch('django_spellbook.management.commands.processing.url_generator.get_clean_url')
    @patch('django_spellbook.management.commands.processing.url_generator.remove_leading_dash')
    def test_generate_url_pattern(self, mock_remove_dash, mock_clean_url, mock_view_name):
        """Test generating URL pattern for a single file."""
        # Configure mocks
        mock_remove_dash.return_value = "test/page"
        mock_clean_url.return_value = "test/page"
        mock_view_name.return_value = "test_page"
        
        # Call method
        url_pattern = self.url_generator._generate_url_pattern(self.processed_file)

        # Check result
        self.assertEqual(url_pattern, "path('test/page/', views.test_page, name='test_page')")
        
    def test_generate_url_patterns(self):
        """Test generating URL patterns for multiple processed files."""
        # Create multiple processed files
        processed_file1 = self.processed_file
        
        processed_file2 = ProcessedFile(
            original_path=Path('/test/file2.md'),
            html_content='<h1>Test 2</h1>',
            template_path=Path('/test/template2.html'),
            relative_url='test/page2',
            context=self.mock_context
        )
        
        # Patch the _generate_url_pattern method
        with patch.object(self.url_generator, '_generate_url_pattern') as mock_generate:
            mock_generate.side_effect = [
                "path('test/page/', test_page, name='test_page')",
                "path('test/page2/', test_page2, name='test_page2')"
            ]
            
            # Call method
            url_patterns = self.url_generator.generate_url_patterns([processed_file1, processed_file2])
            
            # Check results
            self.assertEqual(len(url_patterns), 2)
            self.assertEqual(url_patterns[0], "path('test/page/', test_page, name='test_page')")
            self.assertEqual(url_patterns[1], "path('test/page2/', test_page2, name='test_page2')")
            

from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.url_generator import URLGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext

class TestURLGeneratorExceptions(TestCase):
    """Test exception handling in URLGenerator."""
    
    def test_init_with_invalid_content_app(self):
        """Test initialization with invalid content_app parameter."""
        # Test with empty string
        with self.assertRaises(CommandError) as context:
            URLGenerator("")
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
        
        # Test with None
        with self.assertRaises(CommandError) as context:
            URLGenerator(None)
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
        
        # Test with non-string
        with self.assertRaises(CommandError) as context:
            URLGenerator(123)
        self.assertIn("Content app name must be a non-empty string", str(context.exception))
    
    def test_generate_url_patterns_with_empty_list(self):
        """Test generate_url_patterns with an empty list."""
        url_generator = URLGenerator("test_app")
        
        # Test with empty list - should return empty list
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            result = url_generator.generate_url_patterns([])
            
            self.assertEqual(result, [])
            mock_logger.warning.assert_called_once()
            self.assertIn("No processed files provided", mock_logger.warning.call_args[0][0])
    
    def test_generate_url_patterns_with_invalid_items(self):
        """Test generate_url_patterns with list containing invalid items."""
        url_generator = URLGenerator("test_app")
        
        # Create a list with non-ProcessedFile items
        invalid_items = [
            None,
            "not a processed file",
            123,
            {}
        ]
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            with patch.object(url_generator, '_validate_url_patterns'):  # Skip validation
                result = url_generator.generate_url_patterns(invalid_items)
                
                self.assertEqual(result, [])
                # Should log warnings for each invalid item and one for empty result
                self.assertEqual(mock_logger.warning.call_count, 5)
    
    def test_generate_url_patterns_with_exceptions(self):
        """Test generate_url_patterns handles exceptions from _generate_url_pattern."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Force _generate_url_pattern to raise exception
        with patch.object(url_generator, '_generate_url_pattern', side_effect=ValueError("Test error")):
            with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                with patch.object(url_generator, '_validate_url_patterns'):  # Skip validation
                    result = url_generator.generate_url_patterns([processed_file])
                    
                    self.assertEqual(result, [])
                    mock_logger.error.assert_called_once()
                    self.assertIn("Error generating URL pattern", mock_logger.error.call_args[0][0])
    
    def test_validate_url_patterns_with_duplicates(self):
        """Test _validate_url_patterns detects duplicate paths and names."""
        url_generator = URLGenerator("test_app")
        
        # Create patterns with duplicate paths and names
        patterns = [
            "path('test/page/', test_page, name='test_page')",
            "path('test/page/', test_page_dup, name='test_page_dup')",  # Duplicate path
            "path('other/page/', other_page, name='test_page')"  # Duplicate name
        ]
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            url_generator._validate_url_patterns(patterns)
            
            # Should log 2 warnings (1 for duplicate path, 1 for duplicate name)
            self.assertEqual(mock_logger.warning.call_count, 2)
            warnings = [call[0][0] for call in mock_logger.warning.call_args_list]
            self.assertTrue(any("Duplicate URL path" in w for w in warnings))
            self.assertTrue(any("Duplicate URL name" in w for w in warnings))
    
    def test_validate_url_patterns_with_invalid_patterns(self):
        """Test _validate_url_patterns handles invalid pattern formats."""
        url_generator = URLGenerator("test_app")
        
        # Create patterns with invalid formats
        patterns = [
            "invalid pattern",
            "path('test/page/')",  # Missing name
            "name='test_page')"  # Missing path
        ]
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            url_generator._validate_url_patterns(patterns)
            
            # Should not raise exceptions, but log warnings
            # No warnings because our parsing would skip these
            self.assertEqual(mock_logger.warning.call_count, 0)
    
    def test_validate_url_patterns_with_exceptions(self):
        """Test _validate_url_patterns handles exceptions during validation."""
        url_generator = URLGenerator("test_app")
        
        # Create a pattern that will cause an exception during processing
        # Using None will cause an AttributeError when the code tries to call split()
        pattern = None
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            # This should catch the exception and log a warning
            url_generator._validate_url_patterns([pattern])
            
            # Verify a warning was logged with the correct message
            mock_logger.warning.assert_called_once()
            self.assertIn("Could not validate URL pattern", mock_logger.warning.call_args[0][0])
        
    def test_generate_url_pattern_missing_relative_url(self):
        """Test _generate_url_pattern with ProcessedFile missing relative_url attribute."""
        url_generator = URLGenerator("test_app")
        
        # Create ProcessedFile without relative_url
        mock_context = Mock(spec=SpellbookContext)
        processed_file = Mock(spec=ProcessedFile)
        processed_file.context = mock_context
        
        # Remove relative_url attribute
        if hasattr(processed_file, 'relative_url'):
            delattr(processed_file, 'relative_url')
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            with self.assertRaises(ValueError) as context:
                url_generator._generate_url_pattern(processed_file)
                
            self.assertIn("missing relative_url attribute", str(context.exception))
            mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_empty_relative_url(self):
        """Test _generate_url_pattern with empty relative_url."""
        url_generator = URLGenerator("test_app")
        
        # Create ProcessedFile with empty relative_url
        mock_context = Mock(spec=SpellbookContext)
        processed_file = Mock(spec=ProcessedFile)
        processed_file.context = mock_context
        processed_file.relative_url = ""
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            with self.assertRaises(ValueError) as context:
                url_generator._generate_url_pattern(processed_file)
                
            self.assertIn("missing relative_url attribute", str(context.exception))
            mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_invalid_view_name(self):
        """Test _generate_url_pattern with invalid view name."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Force generate_view_name to return invalid name
        with patch('django_spellbook.management.commands.processing.url_generator.generate_view_name', 
                   return_value=""):
            with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                with self.assertRaises(ValueError) as context:
                    url_generator._generate_url_pattern(processed_file)
                    
                self.assertIn("Could not generate valid view name", str(context.exception))
                mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_non_identifier_view_name(self):
        """Test _generate_url_pattern with view name that's not a valid identifier."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Force generate_view_name to return invalid identifier
        with patch('django_spellbook.management.commands.processing.url_generator.generate_view_name', 
                   return_value="123-invalid"):  # Can't start with number or contain hyphen
            with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                with self.assertRaises(ValueError) as context:
                    url_generator._generate_url_pattern(processed_file)
                    
                self.assertIn("not a valid Python identifier", str(context.exception))
                mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_long_view_name(self):
        """Test _generate_url_pattern with very long view name."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Force generate_view_name to return very long name
        long_name = "a" * 150
        with patch('django_spellbook.management.commands.processing.url_generator.generate_view_name', 
                   return_value=long_name):
            with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                # Should warn but not raise exception
                url_pattern = url_generator._generate_url_pattern(processed_file)
                
                mock_logger.warning.assert_called_once()
                self.assertIn("is quite long", mock_logger.warning.call_args[0][0])
                self.assertIn(long_name, url_pattern)
    
    def test_generate_url_pattern_dangerous_url(self):
        """Test _generate_url_pattern with dangerous URL path."""
        url_generator = URLGenerator("test_app")
        
        # Create processed files with dangerous URLs
        for dangerous_url in ['path/../with/parent/traversal', 'path//with//double/slash']:
            # Create a modified test where we ensure the view name is valid first
            mock_context = Mock(spec=SpellbookContext)
            processed_file = ProcessedFile(
                original_path=Path('/test/file.md'),
                html_content='<h1>Test</h1>',
                template_path=Path('/test/template.html'),
                relative_url='valid_path',  # Use valid path for view name generation
                context=mock_context
            )
            
            # Mock functions in order of calling in the method
            with patch('django_spellbook.management.commands.processing.url_generator.generate_view_name', 
                      return_value="valid_view_name"):  # Ensure valid view name
                with patch('django_spellbook.management.commands.processing.url_generator.get_clean_url', 
                          return_value=dangerous_url):  # Return dangerous URL
                    with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                        with self.assertRaises(ValueError) as context:
                            url_generator._generate_url_pattern(processed_file)
                            
                        self.assertIn("Invalid URL path detected", str(context.exception))
                        mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_invalid_url_name(self):
        """Test _generate_url_pattern with invalid URL name."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='test/page',
            context=mock_context
        )
        
        # Force get_clean_url to return a URL that generates an invalid name
        with patch('django_spellbook.management.commands.processing.url_generator.get_clean_url', 
                  return_value=""):  # Empty URL
            with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
                with self.assertRaises(ValueError) as context:
                    url_generator._generate_url_pattern(processed_file)
                    
                self.assertIn("URL name", str(context.exception))
                mock_logger.error.assert_called_once()
    
    def test_generate_url_pattern_other_exceptions(self):
        """Test _generate_url_pattern handles other exceptions."""
        url_generator = URLGenerator("test_app")
        
        # Create a ProcessedFile that will raise exception when attributes are accessed
        class ExceptionFile:
            @property
            def relative_url(self):
                raise Exception("Test exception")
                
            # Add minimal required attributes
            def __init__(self):
                self.original_path = Path('/test/file.md')
                self.html_content = '<h1>Test</h1>'
                self.template_path = Path('/test/template.html')
                self.context = None
        
        processed_file = ExceptionFile()
        
        with patch('django_spellbook.management.commands.processing.url_generator.logger') as mock_logger:
            with self.assertRaises(ValueError) as context:
                url_generator._generate_url_pattern(processed_file)
                
            self.assertIn("Failed to generate URL pattern", str(context.exception))
            mock_logger.error.assert_called_once()
            
    def test_is_safe_url(self):
        """Test the _is_safe_url method with safe and unsafe URLs."""
        url_generator = URLGenerator("test_app")
        
        # Test safe URLs
        safe_urls = [
            "normal/path",
            "path/with/numbers/123",
            "path/with-dashes",
            "path/with_underscores",
            "path/with.dots",
            "path/with/trailing/slash/"
        ]
        
        for url in safe_urls:
            self.assertTrue(url_generator._is_safe_url(url), f"URL '{url}' should be considered safe")
            
        # Test unsafe URLs
        unsafe_urls = [
            "../path/with/parent/traversal",
            "path//with/double/slash",
            "path/with\x00null/byte",
            "path/with<?php/tag",
            "path/with%20urlencoding"
        ]
        
        for url in unsafe_urls:
            self.assertFalse(url_generator._is_safe_url(url), f"URL '{url}' should be considered unsafe")

    def test_is_safe_url_is_called_during_validation(self):
        """Test that _is_safe_url is called during URL validation."""
        url_generator = URLGenerator("test_app")
        
        # Create a valid ProcessedFile
        mock_context = Mock(spec=SpellbookContext)
        processed_file = ProcessedFile(
            original_path=Path('/test/file.md'),
            html_content='<h1>Test</h1>',
            template_path=Path('/test/template.html'),
            relative_url='valid_path',
            context=mock_context
        )
        
        # Spy on the _is_safe_url method
        with patch.object(url_generator, '_is_safe_url', wraps=url_generator._is_safe_url) as spy:
            url_generator._generate_url_pattern(processed_file)
            
            # Verify _is_safe_url was called at least once
            spy.assert_called_once()