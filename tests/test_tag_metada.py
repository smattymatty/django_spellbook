import unittest
from unittest.mock import patch, Mock, MagicMock
import datetime
from django.conf import settings
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.management.base import CommandError
from django.template.exceptions import TemplateDoesNotExist

from django_spellbook.templatetags.spellbook_tags import (
    show_metadata,
)

class TestShowMetaDataTag(TestCase):
    """Test show_metadata tag."""
    
    def setUp(self):
        """Set up test data."""
        self.basic_metadata = {
            'title': 'Test Page',
            'created_at': '2023-01-01',
            'updated_at': '2023-02-01',
            'url_path': '/test/page/',
            'namespace': 'test_app'
        }
    
    @patch('django_spellbook.templatetags.spellbook_tags.render_to_string')
    @patch('django_spellbook.templatetags.spellbook_tags.get_user_metadata_template')
    def test_show_metadata_for_user_single_app(self, mock_get_template, mock_render):
        """Test show_metadata tag for 'for_user' type with a single app."""
        # Setup mocks
        mock_get_template.return_value = 'test_template.html'
        mock_render.return_value = '<div class="metadata">Test Content</div>'
        
        # Create context
        context = {'metadata': self.basic_metadata}
        
        # Call the tag
        result = show_metadata(context, 'for_user')
        
        # Verify correct template was fetched
        mock_get_template.assert_called_once_with(0)  # 0 is default app index
        
        # Verify render_to_string was called with correct args
        mock_render.assert_called_once_with('test_template.html', {'metadata': self.basic_metadata})
        
        # Verify output
        self.assertEqual(result, '<div class="metadata">Test Content</div>')
    
    @patch('django_spellbook.templatetags.spellbook_tags.render_to_string')
    @patch('django_spellbook.templatetags.spellbook_tags.get_dev_metadata_template')
    def test_show_metadata_for_dev_single_app(self, mock_get_template, mock_render):
        """Test show_metadata tag for 'for_dev' type with a single app."""
        # Setup mocks
        mock_get_template.return_value = 'dev_template.html'
        mock_render.return_value = '<div class="dev-metadata">Dev Content</div>'
        
        # Create context
        context = {'metadata': self.basic_metadata}
        
        # Call the tag
        result = show_metadata(context, 'for_dev')
        
        # Verify correct template was fetched
        mock_get_template.assert_called_once_with(0)  # 0 is default app index
        
        # Verify render_to_string was called with correct args
        mock_render.assert_called_once_with('dev_template.html', {'metadata': self.basic_metadata})
        
        # Verify output
        self.assertEqual(result, '<div class="dev-metadata">Dev Content</div>')
    
    @patch('django_spellbook.templatetags.spellbook_tags.get_current_app_index')
    @patch('django_spellbook.templatetags.spellbook_tags.render_to_string')
    @patch('django_spellbook.templatetags.spellbook_tags.get_user_metadata_template')
    def test_show_metadata_multi_app(self, mock_get_template, mock_render, mock_get_index):
        """Test show_metadata tag with multiple apps."""
        # Setup mocks
        mock_get_index.return_value = 2  # Simulate app index 2
        mock_get_template.return_value = 'app2_template.html'
        mock_render.return_value = '<div class="app2-metadata">App2 Content</div>'
        
        # Create context with app2 namespace
        context = {'metadata': {'namespace': 'app2', 'title': 'App2 Page'}}
        
        # Call the tag
        result = show_metadata(context, 'for_user')
        
        # Verify app index was determined
        mock_get_index.assert_called_once_with(context)
        
        # Verify correct template was fetched with app index
        mock_get_template.assert_called_once_with(2)
        
        # Verify render_to_string called with correct context
        mock_render.assert_called_once_with('app2_template.html', {'metadata': context['metadata']})
        
        # Verify output
        self.assertEqual(result, '<div class="app2-metadata">App2 Content</div>')
    
    @patch('django_spellbook.templatetags.spellbook_tags.get_current_app_index')
    @patch('django_spellbook.templatetags.spellbook_tags.render_to_string')
    @patch('django_spellbook.templatetags.spellbook_tags.get_user_metadata_template')
    def test_show_metadata_no_apps(self, mock_get_template, mock_render, mock_get_index):
        """Test show_metadata tag with no apps configured."""
        # Setup mocks - simulate empty app list
        mock_get_index.return_value = 0  # Default to 0 when no apps
        mock_get_template.return_value = 'default_template.html'
        mock_render.return_value = '<div class="default-metadata">Default Content</div>'
        
        # Create context with empty metadata
        context = {'metadata': {}}
        
        # Call the tag
        result = show_metadata(context, 'for_user')
        
        # Verify app index determination was attempted
        mock_get_index.assert_called_once_with(context)
        
        # Verify default template was used
        mock_get_template.assert_called_once_with(0)
        
        # Verify render_to_string called with empty metadata
        mock_render.assert_called_once_with('default_template.html', {'metadata': {}})
        
        # Verify output
        self.assertEqual(result, '<div class="default-metadata">Default Content</div>')


class TestShowMetaDataTagEdgeCases(TestCase):
    """Test show_metadata tag edge cases."""
    
    def test_show_metadata_invalid_display_type(self):
        """Test show_metadata tag with invalid display type."""
        # Create context
        context = {'metadata': {'title': 'Test'}}
        
        # Call with invalid display type
        result = show_metadata(context, 'invalid_type')
        
        # Verify error message in output
        self.assertTrue(result.startswith("Error: show_metadata tag requires"))
        self.assertIn("got 'invalid_type'", result)
    
    @patch('django_spellbook.templatetags.spellbook_tags.render_to_string')
    @patch('django_spellbook.templatetags.spellbook_tags.get_user_metadata_template')
    def test_show_metadata_template_not_found(self, mock_get_template, mock_render):
        """Test show_metadata tag when template doesn't exist."""
        # Setup mocks
        mock_get_template.return_value = 'non_existent_template.html'
        mock_render.side_effect = TemplateDoesNotExist("non_existent_template.html")
        
        # Create context
        context = {'metadata': {'title': 'Test'}}
        
        # Call the tag
        result = show_metadata(context, 'for_user')
        
        # Verify error message
        self.assertTrue(result.startswith("Error: Metadata template"))
        self.assertIn("non_existent_template.html", result)
    
    @patch('django_spellbook.templatetags.spellbook_tags.get_current_app_index')
    def test_show_metadata_empty_context(self, mock_get_index):
        """Test show_metadata tag with empty context."""
        # Setup mocks
        mock_get_index.return_value = 0
        
        # Call with empty context
        with patch('django_spellbook.templatetags.spellbook_tags.render_to_string') as mock_render:
            mock_render.return_value = '<div>Default</div>'
            result = show_metadata({}, 'for_user')
            
            # Verify render_to_string called with empty metadata
            mock_render.assert_called_once()
            self.assertEqual(mock_render.call_args[0][1]['metadata'], {})
    
    @patch('django_spellbook.templatetags.spellbook_tags.get_current_app_index')
    def test_show_metadata_none_context(self, mock_get_index):
        """Test show_metadata tag with None context."""
        # Setup mocks
        mock_get_index.return_value = 0
        
        # Call with None context
        with patch('django_spellbook.templatetags.spellbook_tags.render_to_string') as mock_render:
            mock_render.return_value = '<div>Default</div>'
            result = show_metadata(None, 'for_user')
            
            # Verify render_to_string called with empty metadata
            mock_render.assert_called_once()
            self.assertEqual(mock_render.call_args[0][1]['metadata'], {})
    
    @patch('django_spellbook.templatetags.spellbook_tags.get_current_app_index')
    def test_show_metadata_render_exception(self, mock_get_index):
        """Test show_metadata tag when render_to_string raises an exception."""
        # Setup mocks
        mock_get_index.return_value = 0
        
        # Call with context that will cause render_to_string to raise exception
        with patch('django_spellbook.templatetags.spellbook_tags.render_to_string') as mock_render:
            mock_render.side_effect = Exception("Unexpected rendering error")
            
            # The tag should handle this gracefully

            result = show_metadata({'metadata': {'title': 'Test'}}, 'for_user')
            
            # Verify error message in result
            self.assertTrue(result.startswith("Error: Failed to render metadata"))