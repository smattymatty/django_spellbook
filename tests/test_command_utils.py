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
        md_paths, md_apps, base_templates = normalize_settings('/test/path', 'test_app', None)

        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        self.assertEqual(base_templates, ['django_spellbook/bases/sidebar_left.html'])
    
    def test_normalize_path_object(self):
        """Test normalizing Path object."""
        path_obj = Path('/test/path')
        md_paths, md_apps, base_templates = normalize_settings(path_obj, 'test_app', "template")
        
        self.assertEqual(md_paths, [path_obj])
        self.assertEqual(md_apps, ['test_app'])
        self.assertEqual(base_templates, ["template"])
    
    def test_normalize_list_values(self):
        """Test normalizing list values."""
        md_paths, md_apps , base_templates = normalize_settings(
            ['/test/path1', '/test/path2'],
            ['app1', 'app2'],
            None
        )

        self.assertEqual(md_paths, ['/test/path1', '/test/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(base_templates, ['django_spellbook/bases/sidebar_left.html', 'django_spellbook/bases/sidebar_left.html'])
    
    def test_normalize_mixed_values(self):
        """Test normalizing mixed values (string and list)."""
        md_paths, md_apps, base_templates = normalize_settings('/test/path', ['app1', 'app2'], "template")
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(base_templates, ["template", "template"])


class TestValidateSpellbookSettings(TestCase):
    """Tests for validate_spellbook_settings function."""

    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_MD_APP='test_app'
    )
    def test_settings_with_new_names(self):
        """Test validation with new setting names."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        self.assertEqual(md_url_prefixes, [''])


    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2']
    )
    def test_settings_with_multiple_pairs(self):
        """Test validation with multiple source-destination pairs."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['', 'app2'])
    
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
        _validate_setting_values(['/test/path'], ['test_app'], ['test_prefix'], [None])
    
    def test_missing_path(self):
        """Test validation with missing path."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values([], ['test_app'], ['test_prefix'], [None])
        
        self.assertIn("SPELLBOOK_MD_PATH", str(context.exception))
    
    def test_missing_app(self):
        """Test validation with missing app."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/test/path'], [], ['test_prefix'], [None])
        
        self.assertIn("SPELLBOOK_MD_APP or SPELLBOOK_CONTENT_APP", str(context.exception))
    
    def test_unequal_lengths(self):
        """Test validation with unequal lengths."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/path1', '/path2'], ['app1'], ['test_prefix'], [None])
        
        self.assertIn("must have the same number of entries", str(context.exception))
    
    def test_empty_path(self):
        """Test validation with empty path."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['', '/path2'], ['app1', 'app2'], ['test_prefix', ''], [None, None])
        
        self.assertIn("Invalid SPELLBOOK_MD_PATH configuration", str(context.exception))
    
    def test_empty_app(self):
        """Test validation with empty app."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/path1', '/path2'], ['app1', ''], ['test_prefix', ''], [None, None])

        self.assertIn("SPELLBOOK_MD_APP must be a non-empty string", str(context.exception))

    @override_settings(INSTALLED_APPS=['django_spellbook'], TESTING=False)
    def test_app_not_in_installed_apps(self):
        """Test validation catches when app is not in INSTALLED_APPS."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(['/path1'], ['missing_app'], ['prefix'], [None])

        error_message = str(context.exception)
        self.assertIn("not in INSTALLED_APPS", error_message)
        self.assertIn("missing_app", error_message)

    @override_settings(INSTALLED_APPS=['django_spellbook', 'django.contrib.auth', 'django.contrib.contenttypes'], TESTING=False)
    def test_multiple_apps_some_not_installed(self):
        """Test validation catches when some apps are not in INSTALLED_APPS."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(
                ['/path1', '/path2', '/path3'],
                ['django.contrib.auth', 'app2', 'django.contrib.contenttypes'],
                ['prefix1', 'prefix2', 'prefix3'],
                [None, None, None]
            )

        error_message = str(context.exception)
        self.assertIn("not in INSTALLED_APPS", error_message)
        self.assertIn("app2", error_message)
        # django.contrib.auth and django.contrib.contenttypes are installed, so they should not be in the error
        self.assertNotIn("django.contrib.auth", error_message.split("not in INSTALLED_APPS")[1])
        self.assertNotIn("django.contrib.contenttypes", error_message.split("not in INSTALLED_APPS")[1])

    @override_settings(INSTALLED_APPS=['django_spellbook', 'django.contrib.auth', 'django.contrib.contenttypes'], TESTING=False)
    def test_all_apps_in_installed_apps(self):
        """Test validation passes when all apps are in INSTALLED_APPS."""
        # This should not raise any exceptions
        _validate_setting_values(
            ['/path1', '/path2'],
            ['django.contrib.auth', 'django.contrib.contenttypes'],
            ['prefix1', 'prefix2'],
            [None, None]
        )


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
            
class TestNormalizeSettingsBaseTemplate(TestCase):
    """Tests for normalize_settings function with focus on base_templates edge cases."""

    def test_empty_base_template_list(self):
        """Test with an empty list for base_templates."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3'],
            ['app1', 'app2', 'app3'],
            []
        )
        # Empty list should be returned as is, which might cause validation issues later
        self.assertEqual(base_templates, [])

    def test_shorter_base_template_list(self):
        """Test with a base_template list shorter than paths/apps."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3'],
            ['app1', 'app2', 'app3'],
            ['template1', 'template2']
        )
        # Should be returned as is, validation should handle length mismatch later
        self.assertEqual(base_templates, ['template1', 'template2'])

    def test_longer_base_template_list(self):
        """Test with a base_template list longer than paths/apps."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2'],
            ['app1', 'app2'],
            ['template1', 'template2', 'template3', 'template4']
        )
        # Should be returned as is, validation should handle length mismatch later
        self.assertEqual(base_templates, ['template1', 'template2', 'template3', 'template4'])

    def test_mixed_none_and_strings_in_list(self):
        """Test with a mixture of None and strings in base_templates list."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3'],
            ['app1', 'app2', 'app3'],
            ['template1', None, 'template3']
        )
        self.assertEqual(base_templates, ['template1', None, 'template3'])

    def test_with_empty_strings_in_list(self):
        """Test with empty strings in base_templates list."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3'],
            ['app1', 'app2', 'app3'],
            ['template1', '', 'template3']
        )
        self.assertEqual(base_templates, ['template1', '', 'template3'])

    def test_with_non_string_values(self):
        """Test with non-string values in base_templates list (should still work)."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3'],
            ['app1', 'app2', 'app3'],
            ['template1', 123, True]  # These non-string values might cause issues elsewhere
        )
        self.assertEqual(base_templates, ['template1', 123, True])

    def test_with_invalid_types(self):
        """Test with completely invalid type for base_templates."""
        # Dictionary instead of list or string
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2'],
            ['app1', 'app2'],
            {'app1': 'template1', 'app2': 'template2'}
        )
        # Should be handled as is, validation might fail later
        self.assertEqual(base_templates, {'app1': 'template1', 'app2': 'template2'})

    def test_with_nested_lists(self):
        """Test with nested lists in base_templates."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2'],
            ['app1', 'app2'],
            [['nested1', 'nested2'], 'template2']
        )
        self.assertEqual(base_templates, [['nested1', 'nested2'], 'template2'])

    def test_single_base_template_for_multiple_paths(self):
        """Test single string template applied to multiple paths."""
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2', '/path3', '/path4'],
            ['app1', 'app2', 'app3', 'app4'],
            'shared_template'
        )
        self.assertEqual(base_templates, ['shared_template', 'shared_template', 'shared_template', 'shared_template'])

    def test_none_base_template_with_no_paths(self):
        """Test None base_template with empty path list."""
        md_paths, md_apps, base_templates = normalize_settings(
            [],
            [],
            None
        )
        # Should use default template even with empty paths
        self.assertEqual(base_templates, ['django_spellbook/bases/sidebar_left.html'])

    def test_string_base_template_with_no_paths(self):
        """Test string base_template with empty path list."""
        md_paths, md_apps, base_templates = normalize_settings(
            [],
            [],
            'template'
        )
        # Should result in empty list since there are no paths
        self.assertEqual(base_templates, [])
        
        
class TestValidateSpellbookSettingsWithBaseTemplate(TestCase):
    """Tests for validate_spellbook_settings function with focus on base_templates."""

    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_MD_APP='test_app',
        SPELLBOOK_MD_BASE_TEMPLATE='base.html',
        TESTING=True
    )
    def test_with_single_base_template(self):
        """Test validation with a single base template."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        self.assertEqual(md_url_prefixes, [''])
        self.assertEqual(base_templates, ['base.html'])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_BASE_TEMPLATE=['base1.html', 'base2.html'],
        TESTING=True
    )
    def test_with_multiple_base_templates(self):
        """Test validation with multiple base templates."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['', 'app2'])
        self.assertEqual(base_templates, ['base1.html', 'base2.html'])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
        SPELLBOOK_MD_APP=['app1', 'app2', 'app3'],
        SPELLBOOK_MD_BASE_TEMPLATE='shared_base.html'
    )
    def test_single_template_for_multiple_paths(self):
        """Test validation with a single template for multiple paths."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2', '/path3'])
        self.assertEqual(md_apps, ['app1', 'app2', 'app3'])
        self.assertEqual(md_url_prefixes, ['', 'app2', 'app3'])
        self.assertEqual(base_templates, ['shared_base.html', 'shared_base.html', 'shared_base.html'])
    
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
        SPELLBOOK_MD_APP=['app1', 'app2', 'app3'],
        SPELLBOOK_MD_BASE_TEMPLATE=['base1.html', 'base2.html']  # One template missing
    )
    def test_with_insufficient_base_templates(self):
        """Test validation with insufficient base templates."""
        with self.assertRaises(CommandError) as context:
            md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()
            
            self.assertIn("SPELLBOOK_MD_BASE_TEMPLATE", str(context.exception))
    
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['custom1', 'custom2'],
        SPELLBOOK_MD_BASE_TEMPLATE=None
    )
    def test_with_custom_url_prefixes_and_none_base_template(self):
        """Test validation with custom URL prefixes and None base template (defaults to sidebar_left.html)."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['custom1', 'custom2'])
        self.assertEqual(base_templates, ['django_spellbook/bases/sidebar_left.html', 'django_spellbook/bases/sidebar_left.html'])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_BASE_TEMPLATE=['base1.html', None]  # Mixed None and string
    )
    def test_with_mixed_none_and_string_templates(self):
        """Test validation with mixed None and string templates."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['', 'app2'])
        self.assertEqual(base_templates, ['base1.html', None])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_BASE_TEMPLATE=''  # Empty string
    )
    def test_with_empty_string_base_template(self):
        """Test validation with empty string base template."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['', 'app2'])
        self.assertEqual(base_templates, ['', ''])

    @override_settings(
        SPELLBOOK_MD_PATH='/single/path',
        SPELLBOOK_MD_APP='single_app',
        SPELLBOOK_MD_BASE_TEMPLATE=['too', 'many', 'templates']
    )
    def test_with_too_many_templates_for_single_path(self):
        """Test validation with too many templates for a single path."""
        with self.assertRaises(CommandError) as context:
            md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()
            
            self.assertIn("SPELLBOOK_MD_BASE_TEMPLATE", str(context.exception))
        
        

class TestValidateSettingValuesWithDangerousTemplates(TestCase):
    """Tests for _validate_setting_values function with focus on dangerous base templates."""

    @override_settings(TESTING=True)
    def test_valid_template_paths(self):
        """Test validation with valid template paths."""
        # These should not raise any exceptions
        valid_templates = [
            'base.html',
            'subfolder/base.html',
            'theme/custom/base.html',
            'base_1.html',
            'base-custom.html',
            None  # None is always valid
        ]

        for template in valid_templates:
            _validate_setting_values(
                ['/test/path'],
                ['test_app'],
                ['prefix'],
                [template]
            )
    
    @override_settings(TESTING=True)
    def test_path_traversal_attempts(self):
        """Test validation catches path traversal attempts."""
        dangerous_traversal_templates = [
            '../base.html',
            '../../base.html',
            '../../../etc/passwd',
            'subfolder/../../../etc/passwd',
            'theme/../../../../etc/shadow',
            'subfolder/./../../secret.txt'
        ]

        from django_spellbook.management.commands.command_utils import _validate_base_templates
        for template in dangerous_traversal_templates:
            with self.assertRaises(CommandError) as context:
                _validate_base_templates([template])
            self.assertIn("dangerous characters", str(context.exception).lower())
    
    @override_settings(TESTING=True)
    def test_absolute_paths(self):
        """Test validation catches absolute paths."""
        absolute_path_templates = [
            '/etc/passwd',
            '/var/www/template.html',
            '/usr/local/etc/config.html',
            'C:\\Windows\\System32\\config.sys',  # Windows path
            '\\\\server\\share\\file.html'  # UNC path
        ]

        from django_spellbook.management.commands.command_utils import _validate_base_templates
        for template in absolute_path_templates:
            with self.assertRaises(CommandError) as context:
                _validate_base_templates([template])
            self.assertIn("contains potentially dangerous characters", str(context.exception).lower())
    
    @override_settings(TESTING=True)
    def test_command_injection_attempts(self):
        """Test validation catches command injection attempts."""
        command_injection_templates = [
            'base.html;rm -rf /',
            'base.html|cat /etc/passwd',
            'base.html && echo "pwned"',
            'base.html`touch /tmp/hacked`',
            'base.html$(ls -la)',
            'base.html > /etc/passwd',
            '`rm -rf /`'
        ]

        from django_spellbook.management.commands.command_utils import _validate_base_templates
        for template in command_injection_templates:
            with self.assertRaises(CommandError) as context:
                _validate_base_templates([template])
            self.assertIn("dangerous characters", str(context.exception).lower())
    
    @override_settings(TESTING=True)
    def test_special_character_templates(self):
        """Test validation catches templates with special characters."""
        special_char_templates = [
            'base<script>alert(1)</script>.html',  # XSS attempt
            'base%00.html',  # Null byte injection
            'base?param=value.html',  # URL parameter
            'base&query=true.html',  # URL ampersand
            'base#fragment.html',  # URL fragment
            'base:alternate.html',  # Colon (dangerous on some systems)
            'base*wildcard.html',  # Wildcard character
            'base(parenthesis).html'  # Parentheses
        ]

        from django_spellbook.management.commands.command_utils import _validate_base_templates
        for template in special_char_templates:
            with self.assertRaises(CommandError) as context:
                _validate_base_templates([template])
            self.assertIn("dangerous characters", str(context.exception).lower())
    
    @override_settings(TESTING=True)
    def test_non_string_templates(self):
        """Test validation catches non-string templates."""
        non_string_templates = [
            123,
            True,
            ['nested', 'list'],
            {'template': 'value'},
            object()
        ]

        from django_spellbook.management.commands.command_utils import _validate_base_templates
        for template in non_string_templates:
            with self.assertRaises(CommandError) as context:
                _validate_base_templates([template])
            self.assertIn("must be None or a string", str(context.exception))
    
    @override_settings(TESTING=True)
    def test_empty_string_template(self):
        """Test validation handles empty string templates."""
        # This might be valid or invalid depending on your implementation
        try:
            _validate_setting_values(
                ['/test/path'],
                ['test_app'],
                ['prefix'],
                ['']
            )
            # If it doesn't raise an exception, no need for assertion
        except CommandError as e:
            # If it should raise an exception, assert the error message
            self.assertIn("empty", str(e).lower())
    
    @override_settings(TESTING=True)
    def test_unusual_unicode_characters(self):
        """Test validation with unusual Unicode characters."""
        unicode_templates = [
            'base\u200Dhidden.html',  # Zero-width joiner (invisible)
            'base\u202Ebidi.html',     # Right-to-left override
            'base\u2028line.html',     # Line separator
            'base\u2029paragraph.html', # Paragraph separator
            'base—emdash.html',        # Em dash
            'base\u3164invisible.html' # Hangul filler (appears as whitespace)
        ]

        for template in unicode_templates:
            # This might be valid or invalid depending on implementation
            try:
                _validate_setting_values(
                    ['/test/path'],
                    ['test_app'],
                    ['prefix'],
                    [template]
                )
                # If allowed, no assertion needed
            except CommandError as e:
                # If not allowed, verify the error message
                self.assertIn("dangerous", str(e).lower())
    
    @override_settings(TESTING=True)
    def test_multiple_templates_one_invalid(self):
        """Test validation when only one template in a list is invalid."""
        from django_spellbook.management.commands.command_utils import _validate_base_templates
        with self.assertRaises(CommandError) as context:
            _validate_base_templates(['valid.html', '../traversal.html', 'also_valid.html'])
        self.assertIn("dangerous characters", str(context.exception).lower())