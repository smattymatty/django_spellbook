# django_spellbook/tests/test_base_template_handling.py

import os
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError

from django_spellbook.management.commands.command_utils import (
    normalize_settings,
    validate_spellbook_settings,
    _validate_setting_values
)


class TestBaseTemplateHandling(TestCase):
    """Tests specific to base template handling."""
    
    def test_normalize_settings_with_base_template(self):
        """Test normalize_settings correctly handles base template."""
        # Test with string template
        md_paths, md_apps, base_templates = normalize_settings(
            '/test/path', 
            'test_app', 
            'custom_base.html'
        )
        self.assertEqual(base_templates, ['custom_base.html'])
        
        # Test with None template
        md_paths, md_apps, base_templates = normalize_settings(
            '/test/path', 
            'test_app', 
            None
        )
        self.assertEqual(base_templates, [None])
        
        # Test with list of templates
        md_paths, md_apps, base_templates = normalize_settings(
            ['/test/path1', '/test/path2'], 
            ['app1', 'app2'], 
            ['base1.html', 'base2.html']
        )
        self.assertEqual(base_templates, ['base1.html', 'base2.html'])
        
        # Test with one string for multiple paths
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2'], 
            ['app1', 'app2'], 
            'shared_base.html'
        )
        self.assertEqual(base_templates, ['shared_base.html', 'shared_base.html'])
        
        # Test with None for multiple paths
        md_paths, md_apps, base_templates = normalize_settings(
            ['/path1', '/path2'], 
            ['app1', 'app2'],
            None
        )
        
        self.assertEqual(base_templates, [None, None])
    
    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_MD_APP='test_app',
        SPELLBOOK_MD_BASE_TEMPLATE='custom_base.html'
    )
    def test_validate_spellbook_settings_with_base_template(self):
        """Test validate_spellbook_settings with base template setting."""
        md_paths, md_apps, md_url_prefixes, base_templates = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        self.assertEqual(md_url_prefixes, [''])
        self.assertEqual(base_templates, ['custom_base.html'])
    
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_BASE_TEMPLATE=['base1.html', 'base2.html']
    )
    def test_validate_spellbook_settings_with_multiple_base_templates(self):
        """Test validate_spellbook_settings with multiple base templates."""
        md_paths, md_apps, md_url_prefixes, base_templates = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(base_templates, ['base1.html', 'base2.html'])
    
    @override_settings(
        SPELLBOOK_MD_PATH=['/path1', '/path2'],
        SPELLBOOK_MD_APP=['app1', 'app2'],
        SPELLBOOK_MD_BASE_TEMPLATE='shared_base.html'
    )
    def test_validate_spellbook_settings_with_shared_base_template(self):
        """Test validate_spellbook_settings with a shared base template."""
        md_paths, md_apps, md_url_prefixes, base_templates = validate_spellbook_settings()
        
        self.assertEqual(md_paths, ['/path1', '/path2'])
        self.assertEqual(md_apps, ['app1', 'app2'])
        self.assertEqual(base_templates, ['shared_base.html', 'shared_base.html'])
    
    def test_validate_setting_values_with_base_templates(self):
        """Test _validate_setting_values with base templates."""
        # This should not raise any error
        _validate_setting_values(
            ['/test/path'],
            ['test_app'],
            ['test_prefix'],
            ['base.html']
        )
        
        # This should not raise any error (None is valid)
        _validate_setting_values(
            ['/test/path'],
            ['test_app'],
            ['test_prefix'],
            [None]
        )
    
    def test_validate_setting_values_with_mismatched_lengths(self):
        """Test _validate_setting_values with mismatched lengths."""
        with self.assertRaises(CommandError):
            _validate_setting_values(
                ['/path1', '/path2'],
                ['app1', 'app2'],
                ['prefix1', 'prefix2'],
                ['base1.html']  # Only one template for two paths
            )
    
    def test_validate_setting_values_with_invalid_template(self):
        """Test _validate_setting_values with invalid template."""
        with self.assertRaises(CommandError):
            _validate_setting_values(
                ['/test/path'],
                ['test_app'],
                ['test_prefix'],
                [123]  # Not a string or None
            )
    
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    @patch('django_spellbook.management.commands.spellbook_md.Command.validate_settings')
    def test_command_passes_base_template_to_processor(self, mock_validate, mock_process):
        """Test that spellbook_md command passes base template to _process_source_destination_pair."""
        # Setup mocks
        mock_validate.return_value = (
            ['/test/path'], 
            ['test_app'], 
            [''], 
            ['custom_base.html']
        )
        mock_process.return_value = 5  # 5 files processed
        
        # Call command
        out = StringIO()
        call_command('spellbook_md', stdout=out)
        
        # Verify _process_source_destination_pair was called with correct base_template
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        self.assertEqual(call_args[0], '/test/path')  # md_path
        self.assertEqual(call_args[1], 'test_app')    # content_app 
        self.assertEqual(call_args[2], '')            # md_url_prefix
        self.assertEqual(call_args[3], 'custom_base.html')  # base_template
    
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    @patch('django_spellbook.management.commands.spellbook_md.Command.validate_settings')
    def test_command_passes_multiple_base_templates(self, mock_validate, mock_process):
        """Test that spellbook_md command passes multiple base templates correctly."""
        # Setup mocks
        mock_validate.return_value = (
            ['/path1', '/path2'], 
            ['app1', 'app2'], 
            ['', 'app2'], 
            ['base1.html', 'base2.html']
        )
        mock_process.return_value = 3  # 3 files processed
        
        # Call command
        out = StringIO()
        call_command('spellbook_md', stdout=out)
        
        # Verify _process_source_destination_pair was called twice with correct base_templates
        self.assertEqual(mock_process.call_count, 2)
        
        # First call should use base1.html
        first_call_args = mock_process.call_args_list[0][0]
        self.assertEqual(first_call_args[0], '/path1')      # md_path
        self.assertEqual(first_call_args[1], 'app1')        # content_app
        self.assertEqual(first_call_args[2], '')            # url_prefix
        self.assertEqual(first_call_args[3], 'base1.html')  # base_template
        
        # Second call should use base2.html
        second_call_args = mock_process.call_args_list[1][0]
        self.assertEqual(second_call_args[0], '/path2')     # md_path
        self.assertEqual(second_call_args[1], 'app2')       # content_app
        self.assertEqual(second_call_args[2], 'app2')       # url_prefix
        self.assertEqual(second_call_args[3], 'base2.html') # base_template
    
    @patch('django_spellbook.management.commands.spellbook_md_p.processor.MarkdownProcessor')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    @patch('django_spellbook.management.commands.spellbook_md.Command.validate_settings')
    def test_base_template_passed_to_markdown_processor(self, mock_validate, mock_process, mock_processor):
        """Test that base_template is passed to the MarkdownProcessor constructor."""
        # Setup mocks
        mock_validate.return_value = (
            ['/test/path'], 
            ['test_app'], 
            [''], 
            ['custom_base.html']
        )
        # Mock the processor instantiation to capture the arguments
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        
        # We'll need to override the actual _process_source_destination_pair method
        # to call our mock constructor
        def side_effect(md_path, content_app, url_prefix, base_template):
            # This would happen inside _process_source_destination_pair
            from django_spellbook.management.commands.command_utils import setup_directory_structure
            with patch('django_spellbook.management.commands.command_utils.setup_directory_structure') as mock_setup:
                mock_setup.return_value = ('/test/app_path', '/test/template_dir')
                # The actual processor instantiation
                processor = mock_processor(
                    content_app=content_app,
                    source_path=md_path,
                    content_dir_path='/test/app_path',
                    template_dir='/test/template_dir',
                    url_prefix=url_prefix,
                    base_template=base_template
                )
            return 5  # Return number of files processed
            
        mock_process.side_effect = side_effect
        
        # Call command
        out = StringIO()
        call_command('spellbook_md', stdout=out)
        
        # Verify MarkdownProcessor was instantiated with correct base_template
        mock_processor.assert_called_once()
        kwargs = mock_processor.call_args[1]
        self.assertEqual(kwargs['content_app'], 'test_app')
        self.assertEqual(kwargs['source_path'], '/test/path')
        self.assertEqual(kwargs['url_prefix'], '')
        self.assertEqual(kwargs['base_template'], 'custom_base.html')