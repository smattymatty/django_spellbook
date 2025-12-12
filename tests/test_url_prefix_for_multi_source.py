# django_spellbook/tests/test_url_prefix_for_multi_source.py

import unittest
from unittest.mock import patch, Mock
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.management.base import CommandError

from django_spellbook.management.commands.command_utils import (
    normalize_url_prefix,
    normalize_url_prefixes,
    validate_spellbook_settings,
    _validate_setting_values
)


class TestURLPrefixUtilityFunctions(TestCase):
    """Test the URL prefix utility functions."""

    def test_normalize_url_prefix(self):
        """Test normalize_url_prefix function."""
        # Test removing leading and trailing slashes
        self.assertEqual(normalize_url_prefix('/test/'), 'test')
        self.assertEqual(normalize_url_prefix('test/'), 'test')
        self.assertEqual(normalize_url_prefix('/test'), 'test')
        self.assertEqual(normalize_url_prefix('test'), 'test')
        
        # Test with multiple slashes
        self.assertEqual(normalize_url_prefix('//test//'), 'test')
        
        # Test with empty string
        self.assertEqual(normalize_url_prefix(''), '')
        
        # Test with only slashes
        self.assertEqual(normalize_url_prefix('/'), '')
        self.assertEqual(normalize_url_prefix('///'), '')

    def test_normalize_url_prefixes(self):
        """Test normalize_url_prefixes function."""
        # Test with None
        self.assertEqual(normalize_url_prefixes(None), [])
        
        # Test with single string
        self.assertEqual(normalize_url_prefixes('test'), ['test'])
        self.assertEqual(normalize_url_prefixes('/test/'), ['test'])
        
        # Test with list of strings
        self.assertEqual(
            normalize_url_prefixes(['test1', 'test2']), 
            ['test1', 'test2']
        )
        self.assertEqual(
            normalize_url_prefixes(['/test1/', '/test2/']), 
            ['test1', 'test2']
        )
        
        # Test with mixed list
        self.assertEqual(
            normalize_url_prefixes(['test1', '/test2/', '//test3//']), 
            ['test1', 'test2', 'test3']
        )
        
        # Test with empty strings in list
        self.assertEqual(
            normalize_url_prefixes(['', '/']), 
            ['', '']
        )


class TestURLPrefixValidation(TestCase):
    """Test URL prefix validation."""

    @override_settings(TESTING=True)
    def test_validate_valid_prefixes(self):
        """Test _validate_setting_values with valid URL prefixes."""
        # Valid prefixes should not raise exceptions
        _validate_setting_values(
            md_file_paths=['/path1', '/path2'],
            content_apps=['app1', 'app2'],
            md_url_prefix=['prefix1', 'prefix2'],
            base_templates=[None, None]
        )
        
        # Empty prefixes are allowed
        _validate_setting_values(
            md_file_paths=['/path1', '/path2'],
            content_apps=['app1', 'app2'],
            md_url_prefix=['', ''],
            base_templates=[None, None]
        )
        
        # Alphanumeric and dash/underscore are allowed
        _validate_setting_values(
            md_file_paths=['/path1', '/path2'],
            content_apps=['app1', 'app2'],
            md_url_prefix=['prefix-1', 'prefix_2'],
            base_templates=[None, None]
        )
        
        # Base templates should be None or strings
        from django_spellbook.management.commands.command_utils import _validate_base_templates
        _validate_base_templates(['template1', None])  # Should not raise

        with self.assertRaises(CommandError):
            _validate_base_templates(['template1', 123])  # Should raise

    @override_settings(TESTING=True)
    def test_validate_dangerous_prefixes(self):
        """Test _validate_setting_values with dangerous URL prefixes."""
        dangerous_prefixes = [
            '..', '//', '<?', '%', '\x00'
        ]
        
        for prefix in dangerous_prefixes:
            with self.assertRaises(CommandError) as context:
                _validate_setting_values(
                    md_file_paths=['/path1'],
                    content_apps=['app1'],
                    md_url_prefix=[prefix],
                    base_templates=[None]
                )
            self.assertIn("contains invalid characters", str(context.exception))

    @override_settings(TESTING=True)
    def test_validate_prefix_count_mismatch(self):
        """Test _validate_setting_values with prefix count mismatch."""
        with self.assertRaises(CommandError) as context:
            _validate_setting_values(
                md_file_paths=['/path1', '/path2'],
                content_apps=['app1', 'app2'],
                md_url_prefix=['prefix1'],  # Only one prefix for two apps
                base_templates=[None, None]
            )
        self.assertIn("must have the same number of entries", str(context.exception))


class TestMultiSourceURLPrefixSettings(TestCase):
    """Test URL prefix settings with multiple sources."""

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['prefix1', 'prefix2'],
        SPELLBOOK_MD_BASE_TEMPLATE=['template1', 'template2'],
        TESTING=True
    )
    def test_explicit_url_prefixes(self):
        """Test with explicitly configured URL prefixes."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['prefix1', 'prefix2'])
        self.assertEqual(base_templates, ['template1', 'template2'])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2', '/path3'],
        SPELLBOOK_MD_APP=['app1', 'app2', 'app3'],
        TESTING=True
    )
    def test_default_url_prefixes_multi_source(self):
        """Test default URL prefixes with multiple sources."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2', '/path3'])
        self.assertEqual(md_apps, ['app1', 'app2', 'app3'])
        # First app should get empty prefix, others should use app name
        self.assertEqual(md_url_prefixes, ['', 'app2', 'app3'])

    @override_settings(
        SPELLBOOK_MD_PATH='/single/path',
        SPELLBOOK_MD_APP='single_app',
        TESTING=True
    )
    def test_default_url_prefix_single_source(self):
        """Test default URL prefix with a single source."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/single/path'])
        self.assertEqual(md_apps, ['single_app'])
        # Single app should get empty prefix
        self.assertEqual(md_url_prefixes, [''])


class TestURLPrefixEdgeCases(TestCase):
    """Test edge cases for URL prefix handling."""

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['', ''],  # Empty prefixes
        TESTING=True
    )
    def test_empty_prefixes(self):
        """Test with empty URL prefixes."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(md_url_prefixes, ['', ''])

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['  ', '  '],  # Whitespace prefixes
        TESTING=True
    )
    def test_whitespace_prefixes(self):
        """Test with whitespace URL prefixes."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        # Whitespace should be preserved (not considered as slashes)
        self.assertEqual(md_url_prefixes, ['  ', '  '])

    @patch('django_spellbook.management.commands.command_utils.logger')
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1'],
        SPELLBOOK_MD_APP=['app1'],
        SPELLBOOK_MD_URL_PREFIX=['invalid$chars'],  # Invalid characters
        TESTING=True
    )
    def test_invalid_characters_warning(self, mock_logger):
        """Test warning for invalid URL prefix characters."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        # Should warn but not raise exception
        self.assertEqual(md_url_prefixes, ['invalid$chars'])
        mock_logger.warning.assert_called_with(
            "URL prefix 'invalid$chars' contains characters that may cause issues with URL routing."
        )

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['/prefix1/', '/prefix2/'],  # Prefixes with slashes
        TESTING=True
    )
    def test_normalize_slash_prefixes(self):
        """Test normalization of URL prefixes with slashes."""
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        # Slashes should be removed
        self.assertEqual(md_url_prefixes, ['prefix1', 'prefix2'])


class TestURLPrefixExceptions(TestCase):
    """Test exception handling for URL prefix validation."""

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX='shared-prefix',  # Single prefix for multiple apps
        TESTING=True
    )
    def test_single_prefix_for_multiple_apps(self):
        """Test using a single prefix string for multiple apps."""
        with self.assertRaises(CommandError) as context:
            validate_spellbook_settings()

        self.assertIn("must have the same number of entries", str(context.exception))

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_URL_PREFIX=['prefix1', 'prefix1'],  # Duplicate prefixes
        TESTING=True
    )
    def test_duplicate_prefixes_warning(self):
        """Test warning for duplicate URL prefixes."""
        with patch('django_spellbook.management.commands.command_utils.logger') as mock_logger:
            md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

            # Should warn but not raise exception
            self.assertEqual(md_url_prefixes, ['prefix1', 'prefix1'])
            # This test verifies that using duplicate prefixes doesn't cause an error,
            # but in a real system they would need to be handled carefully in the URL generation

    @override_settings(
        SPELLBOOK_MD_PATH=['/path1'],
        SPELLBOOK_MD_APP=['app1'],
        SPELLBOOK_MD_URL_PREFIX=['very-long-prefix-' + 'x' * 100],  # Very long prefix
        TESTING=True
    )
    def test_very_long_prefix(self):
        """Test with a very long URL prefix."""
        # Should not raise exception, but could cause issues in URL generation
        md_paths, md_apps, md_url_prefixes, base_templates, _ = validate_spellbook_settings()

        self.assertEqual(len(md_url_prefixes), 1)
        self.assertTrue(len(md_url_prefixes[0]) > 100)