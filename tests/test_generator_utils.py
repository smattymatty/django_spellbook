# django_spellbook/tests/test_generator_utils.py

import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from pathlib import Path
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.generator_utils import (
    remove_leading_dash,
    get_clean_url,
    generate_view_name,
    get_template_path,
    get_spellbook_dir,
    create_file_if_not_exists,
    write_file
)

class TestGeneratorUtils(TestCase):
    
    def test_remove_leading_dash(self):
        """Test removing leading dashes from text."""
        self.assertEqual(remove_leading_dash("--test"), "test")
        self.assertEqual(remove_leading_dash("test"), "test")
        self.assertEqual(remove_leading_dash(""), "")
        self.assertEqual(remove_leading_dash("-"), "")
        
    def test_get_clean_url(self):
        """Test cleaning URL by removing leading dashes."""
        self.assertEqual(get_clean_url("--test/--page"), "test/page")
        self.assertEqual(get_clean_url("test/page"), "test/page")
        self.assertEqual(get_clean_url("--"), "")
        self.assertEqual(get_clean_url(""), "")
        
    def test_generate_view_name(self):
        """Test generating valid Python identifier for view name from URL pattern."""
        self.assertEqual(generate_view_name("test/page"), "view_test_page")
        self.assertEqual(generate_view_name("--test/--page"), "view_test_page")
        self.assertEqual(generate_view_name("test-page"), "view_test_page")
        self.assertEqual(generate_view_name("test_page"), "view_test_page")
        
    def test_generate_view_name_with_numeric_paths(self):
        """Test that generate_view_name properly handles numeric paths."""
        self.assertEqual(generate_view_name("0.1.0-release"), "view_0-1-0_release")
        self.assertEqual(generate_view_name("1.0/docs"), "view_1-0_docs")
        self.assertEqual(generate_view_name("normal-path"), "view_normal_path")
        
    def test_get_template_path(self):
        """Test generating template path from content app and relative URL."""
        self.assertEqual(
            get_template_path("app", "test/page"), 
            os.path.join("app", "spellbook_md", "test/page.html")
        )
        
    @patch('os.path.abspath')
    @patch('os.path.dirname')
    def test_get_spellbook_dir(self, mock_dirname, mock_abspath):
        """Test getting django_spellbook base directory."""
        mock_dirname.return_value = "/fake/path"
        mock_abspath.return_value = "/absolute/fake/path"
        
        result = get_spellbook_dir()
        
        self.assertEqual(result, "/absolute/fake/path")
        
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_file_if_not_exists(self, mock_file, mock_makedirs, mock_exists):
        """Test creating a file when it doesn't exist."""
        mock_exists.return_value = False
        
        create_file_if_not_exists("/path/file.py", "content")
        
        mock_makedirs.assert_called_once_with(os.path.dirname("/path/file.py"), exist_ok=True)
        mock_file.assert_called_once_with("/path/file.py", 'w')
        mock_file().write.assert_called_once_with("content")
        
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_create_file_if_not_exists_error(self, mock_open, mock_makedirs, mock_exists):
        """Test handling error when creating a file."""
        mock_exists.return_value = False
        mock_open.side_effect = IOError("Test error")
        
        with self.assertRaises(CommandError) as context:
            create_file_if_not_exists("/path/file.py", "content")
            
        self.assertIn("Failed to create", str(context.exception))
        
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_file(self, mock_file, mock_makedirs):
        """Test writing content to a file."""
        write_file("/path/file.py", "content")
        
        mock_makedirs.assert_called_once_with(os.path.dirname("/path/file.py"), exist_ok=True)
        mock_file.assert_called_once_with("/path/file.py", 'w')
        mock_file().write.assert_called_once_with("content")