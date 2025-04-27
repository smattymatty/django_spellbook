# django_spellbook/tests/test_discovery.py
import unittest
from unittest.mock import patch, Mock, call
from io import StringIO
from pathlib import Path

from django.test import TestCase

from django_spellbook.management.commands.spellbook_md_p.discovery import (
    discover_blocks,
    find_markdown_files,
    log_and_write
)

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter
class TestDiscoveryFunctions(TestCase):
    """Test basic functionality of the discovery module functions."""
    
    
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.importlib.import_module')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.apps.get_app_configs')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.SpellBlockRegistry._registry', {'block1': Mock(), 'block2': Mock()})
    def test_discover_blocks(self, mock_get_app_configs, mock_import_module):
        """Test the discover_blocks function with successful imports."""
        # Setup mock app configs
        mock_app1 = Mock()
        mock_app1.name = 'app1'
        mock_app2 = Mock()
        mock_app2.name = 'app2'
        mock_get_app_configs.return_value = [mock_app1, mock_app2]
        
        # Clear any existing cache
        if hasattr(discover_blocks, 'cache_clear'):
            discover_blocks.cache_clear()
        
        # Call the function
        stdout = StringIO()
        result = discover_blocks(reporter=MarkdownReporter(stdout))
        
        # Check results
        self.assertEqual(result, 2)
        self.assertIn("Found 2 blocks", stdout.getvalue())
        
        # Verify correct import calls
        mock_import_module.assert_has_calls([
            call('app1.spellblocks'),
            call('app2.spellblocks')
        ])
    
    @patch('os.walk')
    def test_find_markdown_files(self, mock_walk):
        """Test finding markdown files in a directory."""
        # Setup mock file system traversal
        mock_walk.return_value = [
            ('/root', ['dir1', 'dir2'], ['file1.md', 'file2.txt']),
            ('/root/dir1', [], ['file3.md', 'file4.md']),
            ('/root/dir2', [], ['file5.txt'])
        ]
        
        # Mock path validation
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            # Call the function
            results = find_markdown_files('/root')
            
            # Check results - only .md files should be included
            self.assertEqual(len(results), 3)
            self.assertIn(('/root', 'file1.md'), results)
            self.assertIn(('/root/dir1', 'file3.md'), results)
            self.assertIn(('/root/dir1', 'file4.md'), results)
            self.assertNotIn(('/root', 'file2.txt'), results)
            self.assertNotIn(('/root/dir2', 'file5.txt'), results)
    
    @patch('os.walk')
    def test_directory_exclusion_behavior(self, mock_walk):
        """Test the behavior of directory exclusion in find_markdown_files."""
        # Mock a simple directory structure with dirnames that can be modified in-place
        dirnames = ['dir1', 'node_modules']
        mock_walk.return_value = [('/root', dirnames, ['file1.md'])]
        
        # Mock path validation
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            # Call the function with exclusions
            find_markdown_files('/root', exclude_dirs={'node_modules'})
            
            # Verify that dirnames was modified in-place to exclude 'node_modules'
            self.assertNotIn('node_modules', dirnames)
            self.assertIn('dir1', dirnames)


class TestDiscoveryExceptions(TestCase):
    """Test exception handling in the discovery module functions."""
    
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.importlib.import_module')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.apps.get_app_configs')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.SpellBlockRegistry._registry', {})
    def test_discover_blocks_import_error(self, mock_get_app_configs, mock_import_module):
        """Test handling of ImportError during block discovery."""
        # Setup mock app configs
        mock_app1 = Mock()
        mock_app1.name = 'app1'
        mock_app2 = Mock()
        mock_app2.name = 'app2'
        mock_get_app_configs.return_value = [mock_app1, mock_app2]
        
        # Setup import_module to raise ImportError for the first app
        def import_side_effect(module_path):
            if module_path == 'app1.spellblocks':
                raise ImportError("No module named 'app1.spellblocks'")
            return None
        
        mock_import_module.side_effect = import_side_effect
        
        # Clear any existing cache
        if hasattr(discover_blocks, 'cache_clear'):
            discover_blocks.cache_clear()
        
        # Call the function
        stdout = StringIO()
        result = discover_blocks(MarkdownReporter(stdout))
        
        # Function should continue despite ImportError
        self.assertEqual(result, 0)
        self.assertIn("Found 0 blocks", stdout.getvalue())
    
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.importlib.import_module')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.apps.get_app_configs')
    @patch('django_spellbook.management.commands.spellbook_md_p.discovery.SpellBlockRegistry._registry', {})
    def test_discover_blocks_general_exception(self, mock_get_app_configs, mock_import_module):
        """Test handling of general exceptions during block discovery."""
        # Setup mock app configs
        mock_app = Mock()
        mock_app.name = 'app1'
        mock_get_app_configs.return_value = [mock_app]
        
        # Setup import_module to raise a general exception
        mock_import_module.side_effect = Exception("Something went wrong")
        
        # Clear any existing cache
        if hasattr(discover_blocks, 'cache_clear'):
            discover_blocks.cache_clear()
        
        # Call the function
        stdout = StringIO()
        result = discover_blocks(reporter=MarkdownReporter(stdout))
        
        # Function should continue despite the exception
        self.assertEqual(result, 0)
        self.assertIn("Found 0 blocks", stdout.getvalue())
    
    def test_find_markdown_files_nonexistent_path(self):
        """Test behavior when the source path doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                find_markdown_files('/nonexistent/path')
    
    def test_find_markdown_files_not_a_directory(self):
        """Test behavior when the source path is not a directory."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            with self.assertRaises(NotADirectoryError):
                find_markdown_files('/path/to/file.txt')
    
    def test_find_markdown_files_permission_error(self):
        """Test behavior when there's a permission error accessing the directory."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('os.walk', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                find_markdown_files('/protected/path')
    
    def test_find_markdown_files_general_exception(self):
        """Test behavior when there's a general exception during file search."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('os.walk', side_effect=Exception("Something went wrong")):
            with self.assertRaises(Exception):
                find_markdown_files('/problematic/path')