# django_spellbook/tests/test_url_view_generator.py

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from django.core.management.base import CommandError
from django.test import TestCase

from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.management.commands.processing.file_processor import ProcessedFile


class TestURLViewGenerator(TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Initialize with patches for the components
        with patch('django_spellbook.management.commands.processing.url_view_generator.URLGenerator') as mock_url_gen:
            with patch('django_spellbook.management.commands.processing.url_view_generator.ViewGenerator') as mock_view_gen:
                with patch('django_spellbook.management.commands.processing.url_view_generator.FileWriter') as mock_file_writer:
                    self.generator = URLViewGenerator('test_app', '/test/path', '/source/path')
                    
                    # Store the mocks for later use
                    self.mock_url_gen = mock_url_gen.return_value
                    self.mock_view_gen = mock_view_gen.return_value
                    self.mock_file_writer = mock_file_writer.return_value
        
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
        """Test URLViewGenerator initialization."""
        # Check the stored values
        self.assertEqual(self.generator.content_app, 'test_app')
        self.assertEqual(self.generator.content_dir_path, '/test/path')
        self.assertEqual(self.generator.source_path, '/source/path')
        
        # Check the component initializations
        self.assertIsNotNone(self.generator.url_generator)
        self.assertIsNotNone(self.generator.view_generator)
        self.assertIsNotNone(self.generator.file_writer)

    def test_generate_urls_and_views(self):
        """Test generating URLs and views."""
        # Configure the mocks
        self.mock_url_gen.generate_url_patterns.return_value = ["url_pattern1", "url_pattern2"]
        self.mock_view_gen.generate_view_functions.return_value = ["view_function1", "view_function2"]
        
        # Create a sample TOC
        toc = {"test": {"title": "Test"}}
        
        # Call the method
        self.generator.generate_urls_and_views([self.processed_file], toc)
        
        # Verify the calls to the components
        self.mock_url_gen.generate_url_patterns.assert_called_once_with([self.processed_file])
        self.mock_view_gen.generate_view_functions.assert_called_once_with([self.processed_file])
        self.mock_file_writer.write_urls_file.assert_called_once_with(["url_pattern1", "url_pattern2"])
        self.mock_file_writer.write_views_file.assert_called_once_with(["view_function1", "view_function2"], toc)

    def test_generate_urls_and_views_error(self):
        """Test error handling in generate_urls_and_views."""
        # Configure the mock to raise an error
        self.mock_url_gen.generate_url_patterns.side_effect = Exception("Test error")
        
        # Call the method - should raise CommandError
        with self.assertRaises(CommandError) as context:
            self.generator.generate_urls_and_views([self.processed_file], {})
        
        # Check error message
        self.assertIn("Failed to generate URLs and views", str(context.exception))
        self.assertIn("Test error", str(context.exception))
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
        
        # Set up patches for the components used by URLViewGenerator
        patcher1 = patch('django_spellbook.management.commands.processing.url_view_generator.URLGenerator')
        patcher2 = patch('django_spellbook.management.commands.processing.url_view_generator.ViewGenerator')
        patcher3 = patch('django_spellbook.management.commands.processing.url_view_generator.FileWriter')
        self.mock_url_gen = patcher1.start()
        self.mock_view_gen = patcher2.start()
        self.mock_file_writer = patcher3.start()
        
        # Get the mock instances
        self.mock_url_gen_instance = self.mock_url_gen.return_value
        self.mock_view_gen_instance = self.mock_view_gen.return_value
        self.mock_file_writer_instance = self.mock_file_writer.return_value
        
        # Configure URL generator mock to return expected URL patterns
        self.expected_url_patterns = [
            "path('first_blog/', first_blog, name='first_blog')",
            "path('lifestyle/digital-minimalism/', lifestyle_digital_minimalism, name='lifestyle_digital-minimalism')",
            "path('blocks/practice/', blocks_practice, name='blocks_practice')",
            "path('blocks/quote/', blocks_quote, name='blocks_quote')",
            "path('tech/sustainable-tech/', tech_sustainable_tech, name='tech_sustainable-tech')"
        ]
        self.mock_url_gen_instance.generate_url_patterns.return_value = self.expected_url_patterns
        
        # Set up the generator
        self.generator = URLViewGenerator('test_app', os.path.join(self.temp_dir, 'content'))
        
        # Add the patchers to cleanup
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.addCleanup(patcher3.stop)
        
        # Create a mock context for processed files
        self.context = SpellbookContext(
            title='Test',
            published=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            modified=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
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
            self._create_processed_file("----first_blog"),
            self._create_processed_file("lifestyle/--digital-minimalism"),
            self._create_processed_file("blocks/practice"),
            self._create_processed_file("blocks/-quote"),
            self._create_processed_file("tech/sustainable-tech")
        ]
        
        # Generate URLs and views
        self.generator.generate_urls_and_views(processed_files, {})
        
        # Verify URL generator was called with the processed files
        self.mock_url_gen_instance.generate_url_patterns.assert_called_once_with(processed_files)
        
        # Verify FileWriter.write_urls_file was called with the expected URL patterns
        self.mock_file_writer_instance.write_urls_file.assert_called_once_with(self.expected_url_patterns)
        
        # Verify the expected URL patterns match what we want
        self.assertIn("path('first_blog/', first_blog, name='first_blog')", self.expected_url_patterns)
        self.assertIn("path('lifestyle/digital-minimalism/', lifestyle_digital_minimalism, name='lifestyle_digital-minimalism')", self.expected_url_patterns)
        self.assertIn("path('blocks/practice/', blocks_practice, name='blocks_practice')", self.expected_url_patterns)
        self.assertIn("path('blocks/quote/', blocks_quote, name='blocks_quote')", self.expected_url_patterns)
        self.assertIn("path('tech/sustainable-tech/', tech_sustainable_tech, name='tech_sustainable-tech')", self.expected_url_patterns)