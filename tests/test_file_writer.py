# django_spellbook/tests/test_file_writer.py

import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.file_writer import FileWriter

class TestFileWriter(TestCase):
    
    @patch('django_spellbook.management.commands.processing.file_writer.get_spellbook_dir')
    def setUp(self, mock_get_dir):
        """Set up the test environment."""
        mock_get_dir.return_value = "/spellbook/dir"
        
        # Patch file operations to avoid actual file system access
        with patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists'):
            with patch('django_spellbook.management.commands.processing.file_writer.write_file'):
                with patch('os.path.exists', return_value=False):
                    self.file_writer = FileWriter("test_app")
        
    def test_initialization(self):
        """Test initialization of FileWriter."""
        self.assertEqual(self.file_writer.content_app, "test_app")
        self.assertEqual(self.file_writer.spellbook_dir, "/spellbook/dir")
        self.assertEqual(self.file_writer.urls_module, "urls_test_app")
        self.assertEqual(self.file_writer.views_module, "views_test_app")
        
    @patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists')
    def test_ensure_urls_views_files(self, mock_create_file):
        """Test ensuring app-specific URLs and views files exist."""
        self.file_writer._ensure_urls_views_files()
        
        # Should create three files
        self.assertEqual(mock_create_file.call_count, 3)
        
        # Check calls to create_file_if_not_exists
        urls_file_path = os.path.join(self.file_writer.spellbook_dir, "urls_test_app.py")
        views_file_path = os.path.join(self.file_writer.spellbook_dir, "views_test_app.py")
        main_urls_path = os.path.join(self.file_writer.spellbook_dir, "urls.py")
        
        mock_create_file.assert_any_call(urls_file_path, unittest.mock.ANY)
        mock_create_file.assert_any_call(views_file_path, unittest.mock.ANY)
        mock_create_file.assert_any_call(main_urls_path, unittest.mock.ANY)
        
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_update_main_urls_file(self, mock_write, mock_file, mock_exists):
        """Test updating main urls.py with app includes."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "urlpatterns = []"
        
        self.file_writer._update_main_urls_file()
        
        # Should call write_file for main urls.py
        main_urls_path = os.path.join(self.file_writer.spellbook_dir, "urls.py")
        mock_write.assert_called_once_with(main_urls_path, unittest.mock.ANY)
        
        # Check content
        content = mock_write.call_args[0][1]
        self.assertIn("path('', include('django_spellbook.urls_test_app'))", content)
        
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_write_urls_file(self, mock_write_file):
        """Test writing URL patterns to app-specific urls.py file."""
        url_patterns = [
            "path('test/', test_view, name='test')",
            "path('another/', another_view, name='another')"
        ]
        
        self.file_writer.write_urls_file(url_patterns)
        
        # Should write to app-specific urls.py
        urls_file_path = os.path.join(self.file_writer.spellbook_dir, "urls_test_app.py")
        mock_write_file.assert_called_once_with(urls_file_path, unittest.mock.ANY)
        
        # Check content
        content = mock_write_file.call_args[0][1]
        self.assertIn("app_name = 'test_app'", content)
        self.assertIn("path('test/', test_view, name='test')", content)
        
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_write_views_file(self, mock_write_file):
        """Test writing view functions to app-specific views.py file."""
        view_functions = [
            "def test_view(request):\n    return render(request, 'test.html', {})"
        ]
        toc = {"test": {"title": "Test"}}
        
        self.file_writer.write_views_file(view_functions, toc)
        
        # Should write to app-specific views.py
        views_file_path = os.path.join(self.file_writer.spellbook_dir, "views_test_app.py")
        mock_write_file.assert_called_once_with(views_file_path, unittest.mock.ANY)
        
        
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.file_writer import FileWriter

class TestFileWriterExceptions(TestCase):
    """Test exception handling in FileWriter class"""
    
    @patch('django_spellbook.management.commands.processing.file_writer.get_spellbook_dir')
    def setUp(self, mock_get_dir):
        """Set up the test environment."""
        mock_get_dir.return_value = "/spellbook/dir"
        
        # Patch initialization methods to avoid file operations during setup
        with patch.object(FileWriter, '_ensure_urls_views_files'), patch.object(FileWriter, '_update_main_urls_file'):
            self.file_writer = FileWriter("test_app")
    
    @patch('django_spellbook.management.commands.processing.file_writer.create_file_if_not_exists')
    def test_ensure_urls_views_files_exception(self, mock_create_file):
        """Test exception handling when creating initial files fails."""
        # Setup create_file_if_not_exists to raise an exception
        mock_create_file.side_effect = CommandError("Failed to create test file")
        
        # Should propagate the exception
        with self.assertRaises(CommandError) as context:
            self.file_writer._ensure_urls_views_files()
            
        self.assertEqual(str(context.exception), "Failed to create test file")
    
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_update_main_urls_file_read_exception(self, mock_open, mock_exists):
        """Test handling of exception when reading the main urls.py file."""
        mock_exists.return_value = True
        mock_open.side_effect = IOError("Test IO error")
        
        # The method should catch the exception and log it
        with patch('django_spellbook.management.commands.processing.file_writer.logger') as mock_logger:
            with patch('django_spellbook.management.commands.processing.file_writer.write_file'):
                self.file_writer._update_main_urls_file()
                
                # Verify logger.error was called
                mock_logger.error.assert_called_once()
                self.assertIn("Error reading urls.py", mock_logger.error.call_args[0][0])
    
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_update_main_urls_file_write_exception(self, mock_write):
        """Test handling of exception when writing to main urls.py file."""
        mock_write.side_effect = CommandError("Failed to write file")
        
        # Should propagate the exception
        with self.assertRaises(CommandError) as context:
            self.file_writer._update_main_urls_file()
            
        self.assertEqual(str(context.exception), "Failed to write file")
    
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_write_urls_file_exception(self, mock_write):
        """Test exception handling when writing URLs file."""
        mock_write.side_effect = CommandError("Failed to write file")
        
        # Should raise CommandError with appropriate message
        with self.assertRaises(CommandError) as context:
            self.file_writer.write_urls_file(["path('test/', test_view, name='test')"])
            
        self.assertIn("Failed to write URLs file", str(context.exception))
    
    @patch('django_spellbook.management.commands.processing.file_writer.write_file')
    def test_write_views_file_exception(self, mock_write):
        """Test exception handling when writing views file."""
        mock_write.side_effect = CommandError("Failed to write file")
        
        # Should raise CommandError with appropriate message
        with self.assertRaises(CommandError) as context:
            self.file_writer.write_views_file(["def test_view(request): pass"], {})
            
        self.assertIn("Failed to write views file", str(context.exception))
    
    def test_urls_content_generation_exception(self):
        """Test exception handling with invalid URL patterns."""
        # Using a type that can't be joined
        invalid_url_patterns = [None, 123]
        
        with self.assertRaises(Exception):
            self.file_writer.write_urls_file(invalid_url_patterns)
    
    def test_views_content_generation_exception(self):
        """Test exception handling with invalid view functions."""
        # Using objects that can't be joined
        invalid_view_functions = [None, 123]
        
        with self.assertRaises(Exception):
            self.file_writer.write_views_file(invalid_view_functions, {})
            
    def test_error_with_toc_serialization(self):
        """Test exception handling when TOC can't be serialized."""
        # Create a TOC that can't be converted to string representation
        class NonSerializableObject:
            def __str__(self):
                raise ValueError("Cannot convert to string")
                
        invalid_toc = {"problem": NonSerializableObject()}
        
        with self.assertRaises(Exception):
            self.file_writer.write_views_file(["def test_view(request): pass"], invalid_toc)