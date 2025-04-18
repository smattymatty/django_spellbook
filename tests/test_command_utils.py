# django_spellbook/tests/test_command_utils.py

import os
import logging
from io import StringIO
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from django.test import TestCase, override_settings
from django.core.management.base import CommandError

from django_spellbook.management.commands.command_utils import (
    normalize_settings,
    validate_spellbook_settings,
    _validate_setting_values,
    setup_directory_structure,
    setup_template_directory,
    get_folder_list,
    log_and_write
)

class TestNormalizeSettings(TestCase):
    """Tests for normalize_settings function."""

    def test_normalize_string_values(self):
        """Test normalizing string values."""
        md_paths, md_apps = normalize_settings('/test/path', 'test_app')
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
    
    def test_normalize_path_object(self):
        """Test normalizing Path object."""
        path_obj = Path('/test/path')
        md_paths, md_apps = normalize_settings(path_obj, 'test_app')
        
        self.assertEqual(md_paths, [path_obj])
        self.assertEqual(md_apps, ['test_app'])
    
    def test_normalize_list_values(self):
        """Test normalizing list values."""
        md_paths, md_apps = normalize_settings(
            ['/test/path1', '/test/path2'],
            ['app1', 'app2']
        )
        
        self.assertEqual(md_paths, ['/test/path1', '/test/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
    
    def test_normalize_mixed_values(self):
        """Test normalizing mixed values (string and list)."""
        md_paths, md_apps = normalize_settings('/test/path', ['app1', 'app2'])
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['app1', 'app2'])


class TestValidateSpellbookSettings(TestCase):
    """Tests for validate_spellbook_settings function."""

    @override_settings(SPELLBOOK_MD_PATH='/test/path', SPELLBOOK_MD_APP='test_app')
    def test_settings_with_new_names(self):
        """Test validation with new setting names."""
        md_paths, md_apps = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
    
    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_CONTENT_APP='test_app',
        SPELLBOOK_MD_APP=None
    )
    @patch('django_spellbook.management.commands.command_utils.logger')
    def test_settings_with_old_names(self, mock_logger):
        """Test validation with old setting names (deprecated)."""
        md_paths, md_apps = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        
        # Check that we logged a deprecation warning
        mock_logger.warning.assert_called_with(
            "SPELLBOOK_CONTENT_APP is deprecated, use SPELLBOOK_MD_APP instead."
        )
    
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2']
    )
    def test_settings_with_multiple_pairs(self):
        """Test validation with multiple source-destination pairs."""
        md_paths, md_apps = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
    
    @override_settings(
        SPELLBOOK_MD_PATH=None,
        SPELLBOOK_MD_APP=None,
        SPELLBOOK_CONTENT_APP=None
    )
    def test_settings_missing(self):
        """Test validation with missing settings."""
        with self.assertRaises(CommandError) as context:
            validate_spellbook_settings()
        
        self.assertIn("Missing required settings", str(context.exception))


class TestValidateSettingValues(TestCase):
    """Tests for _validate_setting_values function."""

    def test_valid_settings(self):
        """Test validation with valid settings."""
        # This should not raise any exceptions
        _validate_setting_values(['/test/path'], ['test_app'])
    
    def test_missing_path(self):
        """Test validation with missing path."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values([], ['test_app'])
        
        self.assertIn("SPELLBOOK_MD_PATH", str(context.exception))
    
    def test_missing_app(self):
        """Test validation with missing app."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/test/path'], [])
        
        self.assertIn("SPELLBOOK_MD_APP or SPELLBOOK_CONTENT_APP", str(context.exception))
    
    def test_unequal_lengths(self):
        """Test validation with unequal lengths."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/path1', '/path2'], ['app1'])
        
        self.assertIn("must have the same number of entries", str(context.exception))
    
    def test_empty_path(self):
        """Test validation with empty path."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['', '/path2'], ['app1', 'app2'])
        
        self.assertIn("Invalid SPELLBOOK_MD_PATH configuration", str(context.exception))
    
    def test_empty_app(self):
        """Test validation with empty app."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/path1', '/path2'], ['app1', ''])
        
        self.assertIn("SPELLBOOK_MD_APP must be a non-empty string", str(context.exception))


class TestSetupDirectoryStructure(TestCase):
    """Tests for setup_directory_structure function."""

    @patch('os.path.exists')
    @patch('django_spellbook.management.commands.command_utils.setup_template_directory')
    def test_successful_setup(self, mock_setup_template, mock_exists):
        """Test successful directory structure setup."""
        # Setup mocks
        mock_exists.return_value = True
        mock_setup_template.return_value = '/test/app/templates/test_app/spellbook_md'
        
        # Call function
        content_dir_path, template_dir = setup_directory_structure('test_app', '/test/content/file.md')
        
        # Verify results
        self.assertEqual(content_dir_path, '/test/content/test_app')
        self.assertEqual(template_dir, '/test/app/templates/test_app/spellbook_md')
        
        # Verify correct function calls
        mock_exists.assert_called_once_with('/test/content/test_app')
        mock_setup_template.assert_called_once_with('/test/content/test_app', 'test_app')
    
    @patch('os.path.exists')
    def test_content_app_not_found(self, mock_exists):
        """Test error when content app is not found."""
        # Setup mocks
        mock_exists.return_value = False
        
        # Call function
        with self.assertRaises(CommandError) as context:
            setup_directory_structure('test_app', '/test/content/file.md')
        
        # Verify error message
        self.assertIn("Content app test_app not found", str(context.exception))
    
    @patch('os.path.exists')
    @patch('django_spellbook.management.commands.command_utils.setup_template_directory')
    def test_setup_template_error(self, mock_setup_template, mock_exists):
        """Test error when template directory setup fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_setup_template.side_effect = Exception("Template directory error")
        
        # Call function
        with self.assertRaises(CommandError) as context:
            setup_directory_structure('test_app', '/test/content/file.md')
        
        # Verify error message
        self.assertIn("Could not set up content dir path", str(context.exception))
        self.assertIn("Template directory error", str(context.exception))


class TestSetupTemplateDirectory(TestCase):
    """Tests for setup_template_directory function."""

    @patch('pathlib.Path.mkdir')
    def test_successful_setup(self, mock_mkdir):
        """Test successful template directory setup."""
        # Call function
        template_dir = setup_template_directory('/test/app', 'test_app')
        
        # Verify result
        self.assertEqual(template_dir, '/test/app/templates/test_app/spellbook_md')
        
        # Verify directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('pathlib.Path.mkdir')
    def test_directory_creation_error(self, mock_mkdir):
        """Test error when directory creation fails."""
        # Setup mock
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        # Call function
        with self.assertRaises(CommandError) as context:
            setup_template_directory('/test/app', 'test_app')
        
        # Verify error message
        self.assertIn("Could not create template directory", str(context.exception))
        self.assertIn("Permission denied", str(context.exception))


class TestGetFolderList(unittest.TestCase):
    """Tests for get_folder_list function."""

    @patch('django_spellbook.management.commands.command_utils.logger')
    def test_get_folder_list(self, mock_logger):
        """Test getting folder list from path."""
        # Call function
        folders = get_folder_list('/test/content/subfolder/file.md', 'content')
        
        # Verify result
        self.assertEqual(folders, ['file.md', 'subfolder'])
    
    @patch('django_spellbook.management.commands.command_utils.logger')
    def test_get_folder_list_nested(self, mock_logger):
        """Test getting folder list from deeply nested path."""
        # Call function
        folders = get_folder_list('/a/b/c/d/e/f/g.md', 'b')
        
        # Verify result
        self.assertEqual(folders, ['g.md', 'f', 'e', 'd', 'c'])
    
    @patch('django_spellbook.management.commands.command_utils.logger')
    def test_folder_at_root_level(self, mock_logger):
        """Test getting folder list when at root level."""
        # Call function
        folders = get_folder_list('/test/content/file.md', 'content')
        
        # Verify result
        self.assertEqual(folders, ['file.md'])
        
        
class TestLogAndWrite(unittest.TestCase):
    """Tests for log_and_write function."""
    
    def test_log_and_write(self):
        """Test the log_and_write helper function properly logs and writes to stdout."""
        stdout = StringIO()
        
        with patch('django_spellbook.management.commands.command_utils.logger') as mock_logger:
            # Test info level logging
            log_and_write("Info message", 'info', stdout)
            mock_logger.info.assert_called_once_with("Info message")
            self.assertEqual(stdout.getvalue(), "Info message")
            
            # Reset stdout and mock
            stdout = StringIO()
            mock_logger.reset_mock()
            
            # Test debug level logging
            log_and_write("Debug message", 'debug', stdout)
            mock_logger.debug.assert_called_once_with("Debug message")
            self.assertEqual(stdout.getvalue(), "Debug message")
            
            # Test without stdout (should still log)
            mock_logger.reset_mock()
            log_and_write("No stdout message", 'info')
            mock_logger.info.assert_called_once_with("No stdout message")
            