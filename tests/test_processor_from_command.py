# django_spellbook/tests/test_processor.py
import unittest
from unittest.mock import patch, Mock, MagicMock, mock_open
from io import StringIO
from pathlib import Path
import os

from django.test import TestCase

from django_spellbook.management.commands.spellbook_md_p.processor import (
    MarkdownProcessor,
    MarkdownProcessorError,
    TOCBuildingError,
    FileProcessingError
)
from django_spellbook.management.commands.processing.file_processor import (
    ProcessedFile, MarkdownProcessingError
)
from django_spellbook.management.commands.processing.template_generator import TemplateError
from django_spellbook.management.commands.processing.url_view_generator import URLGenerationError
from django_spellbook.markdown.toc import TOCEntry

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

class TestMarkdownProcessor(TestCase):
    """Test normal functionality of the MarkdownProcessor class."""
    
    def setUp(self):
        """Set up common test variables."""
        self.content_app = 'test_app'
        self.source_path = '/test/source'
        self.content_dir_path = '/test/app'
        self.template_dir = '/test/templates'
        self.reporter = MarkdownReporter(StringIO())
        
        # Create MarkdownProcessor with mocked dependencies
        with patch('django_spellbook.management.commands.spellbook_md_p.processor.MarkdownFileProcessor'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.TemplateGenerator'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.URLViewGenerator'):
            self.processor = MarkdownProcessor(
                self.content_app,
                self.source_path,
                self.content_dir_path,
                self.template_dir,
                self.reporter
            )
            
        # Set up mocks for the sub-processors
        self.processor.file_processor = Mock()
        self.processor.template_generator = Mock()
        self.processor.url_generator = Mock()
    
    def test_initialization(self):
        """Test initialization with different types of paths."""
        # Test with string paths
        with patch('django_spellbook.management.commands.spellbook_md_p.processor.MarkdownFileProcessor'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.TemplateGenerator'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.URLViewGenerator'):
            processor = MarkdownProcessor(
                'test_app',
                '/test/source',
                '/test/app',
                '/test/templates',
                self.reporter
            )
            self.assertEqual(processor.content_app, 'test_app')
            self.assertEqual(processor.source_path, Path('/test/source'))
            self.assertEqual(processor.content_dir_path, Path('/test/app'))
            self.assertEqual(processor.template_dir, Path('/test/templates'))
        
        # Test with Path objects
        with patch('django_spellbook.management.commands.spellbook_md_p.processor.MarkdownFileProcessor'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.TemplateGenerator'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.URLViewGenerator'):
            processor = MarkdownProcessor(
                'test_app',
                Path('/test/source'),
                Path('/test/app'),
                Path('/test/templates'),
                self.reporter
            )
            self.assertEqual(processor.content_app, 'test_app')
            self.assertEqual(processor.source_path, Path('/test/source'))
            self.assertEqual(processor.content_dir_path, Path('/test/app'))
            self.assertEqual(processor.template_dir, Path('/test/templates'))
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="---\ntitle: Test Title\n---\nContent")
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.relative_to')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.FrontMatterParser')
    def test_build_toc(self, mock_frontmatter, mock_relative_to, mock_file, mock_walk):
        """Test building the table of contents."""
        # Setup mocks
        mock_walk.return_value = [
            ('/test/source', ['dir1'], ['file1.md', 'file2.txt']),
            ('/test/source/dir1', [], ['---file3.md'])
        ]
        
        # Setup relative_to to return predictable values
        def relative_to_side_effect(base_path):
            path_str = str(mock_relative_to.call_args[0][0])
            if 'file1.md' in path_str:
                return Path('file1.md')
            else:
                return Path('dir1/file3.md')
        
        mock_relative_to.side_effect = relative_to_side_effect
        
        # Setup frontmatter to return metadata with titles
        mock_frontmatter_instance = Mock()
        mock_frontmatter_instance.metadata = {'title': 'Test Title'}
        mock_frontmatter.return_value = mock_frontmatter_instance
        
        # Call the method
        toc = self.processor.build_toc()
        
        # The TOC should be a dict with keys 'title', 'url', and 'children'
        self.assertIn('title', toc)
        self.assertIn('url', toc)
        self.assertIn('children', toc)
        
        # Verify children structure
        children = toc['children']

        
        # Check if dir1 is in the structure
        self.assertIn('dir1', children)
        
        # Verify file3 is in dir1's children
        dir1_children = children['dir1']['children']
        self.assertIn('file3', dir1_children)  # The stem of file3.md
        
        # Verify title for file3
        self.assertEqual(dir1_children['file3']['title'], 'Test Title')
        
        # Veriify url for file3
        self.assertEqual(dir1_children['file3']['url'], 'test_app:dir1_file3')
        
        # Verify the open calls (should be called for each markdown file)
        self.assertEqual(mock_file.call_count, 2)
        
        # Verify frontmatter parser was called for each file
        self.assertEqual(mock_frontmatter.call_count, 2)
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.relative_to')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.get_folder_list')
    def test_process_file(self, mock_get_folder_list, mock_relative_to, mock_exists):
        """Test processing a single markdown file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_folder_list.return_value = ['folder1', 'folder2']
        mock_relative_to.return_value = Path('folder1/folder2/test.md')
        
        # Setup file processor mock
        self.processor.file_processor.process_file.return_value = (
            '<h1>Test</h1>',  # HTML content
            '/test/source/folder1/folder2/test.md',  # Processed path
            MagicMock()  # Context
        )
        
        # Setup template generator mock
        self.processor.template_generator.get_template_path.return_value = 'template/path.html'
        
        # Call the method
        toc = {
            'folder1/folder2/test.md': TOCEntry(Path('folder1/folder2/test.md'), 'Test Title', 'test_app:folder1_folder2_test')
        }
        result = self.processor.process_file('/test/source/folder1/folder2', 'test.md', toc)
        
        # Verify results
        self.assertIsInstance(result, ProcessedFile)
        self.assertEqual(result.original_path, '/test/source/folder1/folder2/test.md')
        self.assertEqual(result.html_content, '<h1>Test</h1>')
        self.assertEqual(result.template_path, 'template/path.html')
        self.assertEqual(result.relative_url, 'folder1/folder2/test')
        
        # Verify method calls
        mock_get_folder_list.assert_called_once_with('/test/source/folder1/folder2', str(self.processor.source_path))
        self.processor.file_processor.process_file.assert_called_once()
        self.processor.template_generator.get_template_path.assert_called_once_with('test.md', ['folder1', 'folder2'])
        self.processor.template_generator.create_template.assert_called_once_with('template/path.html', '<h1>Test</h1>')
    
    def test_generate_urls_and_views(self):
        """Test generating URLs and views."""
        # Setup mocks
        processed_files = [MagicMock(spec=ProcessedFile) for _ in range(3)]
        toc = {'path1': MagicMock(spec=TOCEntry), 'path2': MagicMock(spec=TOCEntry)}
        
        # Call the method
        self.processor.generate_urls_and_views(processed_files, toc)
        
        # Verify method calls
        self.processor.url_generator.generate_urls_and_views.assert_called_once_with(processed_files, toc)
    
    def test_generate_urls_and_views_empty(self):
        """Test generating URLs and views with empty processed files."""
        # Call the method with empty list
        self.processor.generate_urls_and_views([], {})
        
        # Verify no method calls
        self.processor.url_generator.generate_urls_and_views.assert_not_called()


class TestMarkdownProcessorExceptions(TestCase):
    """Test exception handling in the MarkdownProcessor class."""
    
    def setUp(self):
        """Set up common test variables."""
        self.content_app = 'test_app'
        self.source_path = '/test/source'
        self.content_dir_path = '/test/app'
        self.template_dir = '/test/templates'
        self.reporter = MarkdownReporter(StringIO())
        
        # Create MarkdownProcessor with mocked dependencies
        with patch('django_spellbook.management.commands.spellbook_md_p.processor.MarkdownFileProcessor'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.TemplateGenerator'), \
             patch('django_spellbook.management.commands.spellbook_md_p.processor.URLViewGenerator'):
            self.processor = MarkdownProcessor(
                self.content_app,
                self.source_path,
                self.content_dir_path,
                self.template_dir,
                self.reporter
            )
            
        # Set up mocks for the sub-processors
        self.processor.file_processor = Mock()
        self.processor.template_generator = Mock()
        self.processor.url_generator = Mock()
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.os.walk')
    def test_build_toc_os_error(self, mock_walk):
        """Test TOC building error when os.walk fails."""
        # Setup mock to raise exception
        mock_walk.side_effect = OSError("Permission denied")
        
        # Verify exception is caught and re-raised
        with self.assertRaises(TOCBuildingError):
            self.processor.build_toc()
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.os.walk')
    @patch('builtins.open')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.TOCGenerator')
    def test_build_toc_file_error(self, mock_toc_generator_class, mock_open, mock_walk):
        """Test TOC building error when file cannot be read."""
        # Setup mocks
        mock_walk.return_value = [('/test/source', [], ['file1.md'])]
        mock_open.side_effect = IOError("Cannot read file")
        
        # Mock TOCGenerator and its instance
        mock_toc_generator = Mock()
        mock_toc_generator_class.return_value = mock_toc_generator
        
        # Setup the mock TOC that will be returned - empty because file read failed
        mock_toc = {}
        mock_toc_generator.get_toc.return_value = mock_toc
        
        # Verify exception in file read is caught and function continues
        toc = self.processor.build_toc()
        self.assertEqual(len(toc), 0)  # No entries due to file error
        
        # Verify get_toc was called despite file error
        mock_toc_generator.get_toc.assert_called_once()
        # Verify add_entry was not called (couldn't read the file)
        mock_toc_generator.add_entry.assert_not_called()
        
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists')
    def test_process_file_not_exists(self, mock_exists):
        """Test processing file that doesn't exist."""
        # Setup mock
        mock_exists.return_value = False
        
        # Call method and verify exception
        with self.assertRaises(FileProcessingError):
            self.processor.process_file('/test/source', 'nonexistent.md', {})
    
    def test_process_file_not_markdown(self):
        """Test processing file that is not a markdown file."""
        # Call method with non-markdown file
        with patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists', return_value=True):
            with self.assertRaises(FileProcessingError):
                self.processor.process_file('/test/source', 'file.txt', {})
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.get_folder_list')
    def test_process_file_processing_error(self, mock_get_folder_list, mock_exists):
        """Test error during markdown processing."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_folder_list.return_value = ['folder']
        
        # Setup file processor to raise exception
        self.processor.file_processor.process_file.side_effect = MarkdownProcessingError("Processing error")
        
        # Call method and verify exception
        with self.assertRaises(FileProcessingError):
            self.processor.process_file('/test/source', 'file.md', {})
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.get_folder_list')
    def test_process_file_template_error(self, mock_get_folder_list, mock_exists):
        """Test error during template creation."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_folder_list.return_value = ['folder']
        
        # Setup file processor and template generator
        self.processor.file_processor.process_file.return_value = (
            '<h1>Test</h1>',  # HTML content
            '/test/source/file.md',  # Processed path
            MagicMock()  # Context
        )
        self.processor.template_generator.get_template_path.return_value = 'template/path.html'
        self.processor.template_generator.create_template.side_effect = TemplateError("Template error")
        
        # Call method and verify exception
        with self.assertRaises(FileProcessingError):
            self.processor.process_file('/test/source', 'file.md', {})
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.Path.exists')
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.get_folder_list')
    def test_process_file_unexpected_error(self, mock_get_folder_list, mock_exists):
        """Test unexpected error during file processing."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_folder_list.return_value = ['folder']
        
        # Setup file processor to raise unexpected exception
        self.processor.file_processor.process_file.side_effect = ValueError("Unexpected error")
        
        # Call method and verify exception
        with self.assertRaises(FileProcessingError):
            self.processor.process_file('/test/source', 'file.md', {})
    
    def test_generate_urls_and_views_error(self):
        """Test error during URL and view generation."""
        # Setup processed files and TOC
        processed_files = [MagicMock(spec=ProcessedFile) for _ in range(2)]
        toc = {'path': MagicMock(spec=TOCEntry)}
        
        # Setup URL generator to raise exception
        self.processor.url_generator.generate_urls_and_views.side_effect = URLGenerationError("URL generation error")
        
        # Call method and verify exception
        with self.assertRaises(MarkdownProcessorError):
            self.processor.generate_urls_and_views(processed_files, toc)
    
    def test_generate_urls_and_views_unexpected_error(self):
        """Test unexpected error during URL and view generation."""
        # Setup processed files and TOC
        processed_files = [MagicMock(spec=ProcessedFile) for _ in range(2)]
        toc = {'path': MagicMock(spec=TOCEntry)}
        
        # Setup URL generator to raise unexpected exception
        self.processor.url_generator.generate_urls_and_views.side_effect = ValueError("Unexpected error")
        
        # Call method and verify exception
        with self.assertRaises(MarkdownProcessorError):
            self.processor.generate_urls_and_views(processed_files, toc)