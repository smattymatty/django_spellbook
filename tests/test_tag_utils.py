import unittest
from unittest.mock import patch, Mock, MagicMock
import datetime
from django.conf import settings
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.management.base import CommandError

import django_spellbook


from django_spellbook.templatetags.tag_utils import (
    get_metadata_template, 
    get_user_metadata_template, 
    get_dev_metadata_template, 
    get_current_app_index,
    get_installed_apps
)

class TestTagUtils(TestCase):
    """Tests for the tag_utils module."""
    
    def test_get_metadata_template_with_no_settings(self):
        """Test get_metadata_template with no settings."""
        # Test with default settings (None)
        with self.settings(SPELLBOOK_MD_METADATA_BASE=None):
            # Should return default templates
            self.assertEqual(
                get_metadata_template('for_user'), 
                'django_spellbook/metadata/for_user.html'
            )
            self.assertEqual(
                get_metadata_template('for_dev'), 
                'django_spellbook/metadata/for_dev.html'
            )
    
    def test_get_metadata_template_with_tuple_setting(self):
        """Test get_metadata_template with tuple setting."""
        # Override with a tuple setting
        with self.settings(SPELLBOOK_MD_METADATA_BASE=('custom_user.html', 'custom_dev.html')):
            # Should return the custom templates
            self.assertEqual(get_metadata_template('for_user'), 'custom_user.html')
            self.assertEqual(get_metadata_template('for_dev'), 'custom_dev.html')
    
    @override_settings(SPELLBOOK_MD_METADATA_BASE=[
        ('app1_user.html', 'app1_dev.html'),
        ('app2_user.html', 'app2_dev.html'),
        ('app3_user.html', 'app3_dev.html')
    ])
    def test_get_metadata_template_with_list_setting(self):
        """Test get_metadata_template with list setting."""
        # Test different app indices
        self.assertEqual(get_metadata_template('for_user', 0), 'app1_user.html')
        self.assertEqual(get_metadata_template('for_dev', 0), 'app1_dev.html')
        
        self.assertEqual(get_metadata_template('for_user', 1), 'app2_user.html')
        self.assertEqual(get_metadata_template('for_dev', 1), 'app2_dev.html')
        
        self.assertEqual(get_metadata_template('for_user', 2), 'app3_user.html')
        self.assertEqual(get_metadata_template('for_dev', 2), 'app3_dev.html')
    
    @override_settings(SPELLBOOK_MD_METADATA_BASE=[
        ('app1_user.html', 'app1_dev.html'),
        ('app2_user.html', 'app2_dev.html')
    ])
    def test_get_metadata_template_with_out_of_bounds_index(self):
        """Test get_metadata_template with out of bounds index."""
        # Test with index out of range - should log a warning and use default
        with self.assertLogs(level='WARNING'):
            self.assertEqual(
                get_metadata_template('for_user', 5), 
                'django_spellbook/metadata/for_user.html'
            )
    
    def test_get_metadata_template_with_invalid_type(self):
        """Test get_metadata_template with invalid display type."""
        # Test with invalid display type
        with self.assertRaises(ValueError):
            get_metadata_template('invalid_type')
    
    @override_settings(SPELLBOOK_MD_METADATA_BASE=[
        'invalid_format',  # Not a tuple
        ('valid_user.html', 'valid_dev.html')
    ])
    def test_get_metadata_template_with_invalid_format(self):
        """Test get_metadata_template with invalid format in settings."""
        # Test with invalid format in settings - should log a warning and use default
        with self.assertLogs(level='WARNING'):
            self.assertEqual(
                get_metadata_template('for_user', 0), 
                'django_spellbook/metadata/for_user.html'
            )
    
    def test_get_user_metadata_template(self):
        """Test get_user_metadata_template."""
        with patch('django_spellbook.templatetags.tag_utils.get_metadata_template') as mock_get:
            get_user_metadata_template(1)
            mock_get.assert_called_once_with('for_user', 1)
    
    def test_get_dev_metadata_template(self):
        """Test get_dev_metadata_template."""
        with patch('django_spellbook.templatetags.tag_utils.get_metadata_template') as mock_get:
            get_dev_metadata_template(2)
            mock_get.assert_called_once_with('for_dev', 2)
    
    def test_get_current_app_index(self):
        """Test get_current_app_index."""
        # Mock the get_installed_apps function
        with patch('django_spellbook.templatetags.tag_utils.get_installed_apps') as mock_get_apps:
            # Test with single app configuration
            mock_get_apps.return_value = 'single_app'
            
            # When SPELLBOOK_MD_APP is a string (single app)
            context = {'metadata': {'namespace': 'single_app'}}
            self.assertEqual(get_current_app_index(context), 0)
            
            # Test with multiple app configuration
            mock_get_apps.return_value = ['app1', 'app2', 'app3']
            
            # When namespace matches first app
            context = {'metadata': {'namespace': 'app1'}}
            self.assertEqual(get_current_app_index(context), 0)
            
            # When namespace matches second app
            context = {'metadata': {'namespace': 'app2'}}
            self.assertEqual(get_current_app_index(context), 1)
            
            # When namespace matches third app
            context = {'metadata': {'namespace': 'app3'}}
            self.assertEqual(get_current_app_index(context), 2)
            
            # When namespace doesn't match any app
            context = {'metadata': {'namespace': 'unknown_app'}}
            self.assertEqual(get_current_app_index(context), 0)
            
            # When no namespace in metadata
            context = {'metadata': {}}
            self.assertEqual(get_current_app_index(context), 0)
            
            # When no metadata in context
            context = {}
            self.assertEqual(get_current_app_index(context), 0)
            
    def test_get_current_app_index_real_edge_cases(self):
        """Test get_current_app_index with real edge cases."""
        # Save original method to restore later
        original_get_installed_apps = getattr(
            django_spellbook.templatetags.tag_utils, 'get_installed_apps'
        )
        
        try:
            # Test case 1: SPELLBOOK_MD_APP is a string (single app)
            # This should return 0 regardless of the namespace
            def mock_get_apps_string():
                return 'single_app'
                
            # Monkey patch the function
            django_spellbook.templatetags.tag_utils.get_installed_apps = mock_get_apps_string
            
            # Even if namespace doesn't match, it should return 0 for single app
            context = {'metadata': {'namespace': 'different_app'}}
            self.assertEqual(get_current_app_index(context), 0, 
                            "Should return 0 for single app config regardless of namespace")
            
            # Test case 2: SPELLBOOK_MD_APP is an empty list
            # This should safely return 0 without causing IndexError
            def mock_get_apps_empty():
                return []
                
            django_spellbook.templatetags.tag_utils.get_installed_apps = mock_get_apps_empty
            
            context = {'metadata': {'namespace': 'any_app'}}
            self.assertEqual(get_current_app_index(context), 0,
                            "Should return 0 for empty app list")
            
            # Test case 3: SPELLBOOK_MD_APP is None
            # This should safely return 0 without errors
            def mock_get_apps_none():
                return None
                
            django_spellbook.templatetags.tag_utils.get_installed_apps = mock_get_apps_none
            
            context = {'metadata': {'namespace': 'any_app'}}
            self.assertEqual(get_current_app_index(context), 0,
                            "Should return 0 if SPELLBOOK_MD_APP is None")
            
            # Test case 4: Namespace contains special characters or is unusually formatted
            def mock_get_apps_list():
                return ['normal_app', 'app-with-dashes', 'app_123']
                
            django_spellbook.templatetags.tag_utils.get_installed_apps = mock_get_apps_list
            
            context = {'metadata': {'namespace': 'app-with-dashes'}}
            self.assertEqual(get_current_app_index(context), 1,
                            "Should correctly match app with dashes")
            
            context = {'metadata': {'namespace': 'app_123'}}
            self.assertEqual(get_current_app_index(context), 2,
                            "Should correctly match app with numbers")
            
            # Test case 5: metadata value is not a dict with expected structure
            def mock_get_apps_regular():
                return ['app1', 'app2']
                
            django_spellbook.templatetags.tag_utils.get_installed_apps = mock_get_apps_regular
            
            # Metadata is a string instead of dict
            context = {'metadata': 'not-a-dict'}
            self.assertEqual(get_current_app_index(context), 0,
                            "Should safely return 0 if metadata is not a dict")
            
            # Metadata dict with unexpected structure
            context = {'metadata': {'different_key': 'app1'}}
            self.assertEqual(get_current_app_index(context), 0,
                            "Should return 0 if namespace not in metadata")
            
            # Empty context dictionary
            self.assertEqual(get_current_app_index({}), 0,
                            "Should handle empty context")
            
            # None context
            self.assertEqual(get_current_app_index(None), 0,
                            "Should handle None context")
            
        finally:
            # Restore the original method
            django_spellbook.templatetags.tag_utils.get_installed_apps = original_get_installed_apps
            
    def test_get_installed_apps(self):
        """Test get_installed_apps function with various settings configurations."""
        
        # Test case 1: SPELLBOOK_MD_APP is a string
        with self.settings(SPELLBOOK_MD_APP='test_app'):
            self.assertEqual(get_installed_apps(), 'test_app')
        
        # Test case 2: SPELLBOOK_MD_APP is a list
        app_list = ['app1', 'app2', 'app3']
        with self.settings(SPELLBOOK_MD_APP=app_list):
            self.assertEqual(get_installed_apps(), app_list)
        
        # Test case 3: SPELLBOOK_MD_APP is None
        with self.settings(SPELLBOOK_MD_APP=None):
            with self.assertLogs(level='WARNING') as logs:
                result = get_installed_apps()
                self.assertEqual(result, [])
                self.assertTrue(any("SPELLBOOK_MD_APP is not set" in log for log in logs.output))
        
        # Test case 4: SPELLBOOK_MD_APP setting doesn't exist
        # First save original SPELLBOOK_MD_APP if it exists
        has_setting = hasattr(settings, 'SPELLBOOK_MD_APP')
        original_value = getattr(settings, 'SPELLBOOK_MD_APP', None) if has_setting else None
        
        try:
            # Remove the setting if it exists
            if has_setting:
                delattr(settings, 'SPELLBOOK_MD_APP')
            
            with self.assertLogs(level='WARNING') as logs:
                result = get_installed_apps()
                self.assertEqual(result, [])
                self.assertTrue(any("SPELLBOOK_MD_APP is not set" in log for log in logs.output))
        finally:
            # Restore the original setting if it existed
            if has_setting:
                setattr(settings, 'SPELLBOOK_MD_APP', original_value)
        
        # Test case 5: Exception scenario
        # We'll mock getattr to raise an exception
        with patch('django_spellbook.templatetags.tag_utils.getattr') as mock_getattr:
            mock_getattr.side_effect = Exception("Test exception")
            
            with self.assertLogs(level='ERROR') as logs:
                result = get_installed_apps()
                self.assertEqual(result, [])
                self.assertTrue(any("Error getting SPELLBOOK_MD_APP from settings" in log for log in logs.output))
                self.assertTrue(any("Test exception" in log for log in logs.output))