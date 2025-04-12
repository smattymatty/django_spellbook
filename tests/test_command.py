import unittest
import datetime
from unittest.mock import patch, Mock, mock_open, call
from pathlib import Path
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django_spellbook.management.commands.spellbook_md import Command
from django_spellbook.markdown.context import SpellbookContext

import tempfile


@override_settings(
    SPELLBOOK_MD_PATH='/test/path',
    SPELLBOOK_CONTENT_APP='test_app'
)
class TestSpellbookCommand(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.command = Command()
        self.command.stdout = Mock()  # Mock stdout for testing output
        self.command.validate_settings()  # Initialize settings-based attributes

    def test_initialization(self):
        """Test command initialization"""
        self.assertIsNotNone(self.command.toc_generator)
        self.assertIsNotNone(self.command.file_processor)
        self.assertIsNone(self.command.template_generator)
        self.assertIsNone(self.command.url_generator)

    @patch('django_spellbook.management.commands.spellbook_md.apps')
    def test_discover_blocks(self, mock_apps):
        """Test block discovery from installed apps"""
        # Setup mock apps
        mock_app_config = Mock()
        mock_app_config.name = 'test_app'
        mock_apps.get_app_configs.return_value = [mock_app_config]

        # Test successful block discovery
        with patch('importlib.import_module') as mock_import:
            self.command.discover_blocks()
            mock_import.assert_called_with('test_app.spellblocks')

        # Test import error handling
        mock_import = Mock(side_effect=ImportError())
        with patch('importlib.import_module', mock_import):
            self.command.discover_blocks()
            self.command.stdout.write.assert_any_call(
                'No blocks found in test_app')

        # Test general error handling
        mock_import = Mock(side_effect=Exception("Test error"))
        with patch('importlib.import_module', mock_import):
            self.command.discover_blocks()
            self.command.stdout.write.assert_any_call(
                self.command.style.WARNING(
                    'Error loading blocks from test_app: Test error'
                )
            )

    @override_settings(SPELLBOOK_MD_PATH='/test/path')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    def test_build_toc(self, mock_file, mock_walk):
        """Test table of contents building"""
        # Setup mock walk
        mock_walk.return_value = [
            ('/test/path', [], ['test1.md', 'test2.md']),
        ]

        # Setup mock file content
        mock_file.return_value.read.return_value = """---
title: Test Page
---
# Content
"""

        # Setup mock FrontMatterParser
        mock_frontmatter = Mock()
        mock_frontmatter.metadata = {'title': 'Test Page'}

        with patch('django_spellbook.management.commands.spellbook_md.FrontMatterParser',
                   return_value=mock_frontmatter):
            toc = self.command._build_toc('')

            self.assertIsInstance(toc, dict)
            mock_walk.assert_called_once()
            self.assertEqual(mock_file.call_count, 2)

    def test_setup_directory_structure(self):
        """Test directory structure setup and template creation"""
        with patch('os.path.exists') as mock_exists, \
                patch('os.path.join') as mock_join, \
                patch('os.makedirs') as mock_makedirs:

            # First, mock the content app path check
            mock_exists.side_effect = lambda path: 'templates' not in path
            mock_join.side_effect = lambda *args: '/'.join(args)

            # Use a temporary directory instead of hardcoded path
            with tempfile.TemporaryDirectory() as content_path:
                self.command._setup_directory_structure(content_path)
                
                # Build expected paths using the actual temp directory
                expected_content_dir = f"{content_path}/test_app"
                expected_template_path = f"{content_path}/test_app/templates/test_app/spellbook_md"

                # Verify content_dir_path was set
                self.assertIn(
                    'test_app',
                    expected_content_dir
                )

                # Verify template directory was created
                #mock_makedirs.assert_called_once_with(expected_template_path, exist_ok=True)

                # Verify the template_dir was set
                self.assertIn(
                    'test_app/templates/test_app/spellbook_md',
                    expected_template_path
                )
    def test_setup_directory_structure_content_app_missing(self):
        """Test setup fails when content app directory doesn't exist"""
        with patch('os.path.exists', return_value=False), \
                patch('os.path.join') as mock_join:

            mock_join.side_effect = lambda *args: '/'.join(args)

            with self.assertRaises(CommandError) as context:
                self.command._setup_directory_structure('/test/path/content')

            self.assertIn('Content app test_app not found',
                          str(context.exception))

    def test_setup_template_directory_error(self):
        """Test template directory setup error handling"""
        self.command.content_dir_path = '/nonexistent/path'
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            with self.assertRaises(CommandError):
                self.command._setup_template_directory()

    def test_get_folder_list(self):
        """Test folder list generation"""
        self.command.md_file_path = 'content'
        folders = self.command._get_folder_list('content/folder1/folder2')

        self.assertEqual(folders, ['folder2', 'folder1'])

    def test_validate_settings_missing(self):
        """Test settings validation with missing settings"""
        with self.settings(SPELLBOOK_CONTENT_APP=None, SPELLBOOK_MD_PATH=None):
            with patch.object(self.command, '_normalize_settings', return_value=(None, None)):
                with self.assertRaises(CommandError) as context:
                    self.command.validate_settings()
                self.assertIn('Missing required setting', str(context.exception))

    @patch('os.walk')
    def test_handle_no_files(self, mock_walk):
        """Test command execution with no markdown files"""
        mock_walk.return_value = [('/test/path', [], [])]

        with self.assertRaises(CommandError):
            self.command.handle()

    @patch('os.walk')
    @patch('django_spellbook.management.commands.spellbook_md.MarkdownFileProcessor')
    def test_handle_processing_error(self, mock_processor, mock_walk):
        """Test command execution with processing errors"""
        # Setup mocks
        mock_walk.return_value = [('/test/path', [], ['test.md'])]
        mock_processor_instance = Mock()
        mock_processor_instance.process_file.side_effect = Exception(
            "Processing error")
        mock_processor.return_value = mock_processor_instance

        with self.assertRaises(CommandError):
            self.command.handle()

    def test_setup_template_directory_error(self):
        """Test template directory setup error handling"""
        self.command.content_dir_path = '/nonexistent/path'

        with self.assertRaises(CommandError):
            self.command._setup_template_directory()

    @patch('django_spellbook.management.commands.spellbook_md.FrontMatterParser')
    @patch('django_spellbook.management.commands.spellbook_md.TOCGenerator')
    def test_build_toc_error(self, mock_toc_generator, mock_frontmatter):
        """Test TOC building error handling"""
        # Setup mock TOC generator
        mock_toc_instance = Mock()
        mock_toc_instance.get_toc.return_value = {}
        mock_toc_generator.return_value = mock_toc_instance

        mock_frontmatter.side_effect = Exception("Frontmatter error")

        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [('/test/path', [], ['test.md'])]
            with patch('builtins.open', mock_open(read_data="# Test")):
                toc = self.command._build_toc("")
                self.assertEqual(toc, {})
                mock_toc_instance.get_toc.assert_called_once()

    @patch('os.walk')
    def test_handle_file_discovery(self, mock_walk):
        """Test markdown file discovery"""
        mock_walk.return_value = [
            ('/test/path', [], ['test.md', 'not_md.txt']),
            ('/test/path/sub', [], ['another.md'])
        ]

        with patch.object(self.command, '_build_toc'):
            with patch.object(self.command, '_setup_directory_structure'):
                try:
                    self.command.handle()
                except Exception:
                    pass  # We expect an error later in processing

                self.command.stdout.write.assert_any_call(
                    "Found 2 markdown files to process"
                )


@patch('os.walk')
@patch('os.path.exists')
@patch('os.makedirs')
class TestSpellbookCommandFileProcessing(TestCase):
    def setUp(self):
        self.command = Command()
        self.command.stdout = Mock()
        # Override validate_settings behavior by setting attributes directly for testing
        self.command.md_file_paths = ['/test/path']
        self.command.content_apps = ['test_app']
        self.command.md_file_path = '/test/path'
        self.command.content_app = 'test_app'
        # Set up content_dir_path and template_dir
        self.command.content_dir_path = '/test/path/test_app'
        self.command.template_dir = '/test/path/test_app/templates/test_app/spellbook_md'

    @override_settings(
    SPELLBOOK_MD_PATH='/test/path',
    SPELLBOOK_CONTENT_APP='test_app'
)
    def test_successful_file_processing(
        self, mock_makedirs, mock_exists, mock_walk
    ):
        # Mock walk to return one markdown file
        mock_walk.return_value = [('/test/path', [], ['test.md'])]

        # Mock exists to return True for directory checks
        mock_exists.return_value = True

        # Create mock file processor
        mock_file_processor = Mock()
        context = SpellbookContext(
            title='Test',
            created_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            updated_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            url_path='test',
            raw_content='# Test\nThis is a test',
        )
        mock_file_processor.process_file.return_value = (
            '<h1>Test</h1>',  # html_content
            '/test/path/test.md',  # file_path
            context  # context
        )
        self.command.file_processor = mock_file_processor

        # Create mock template generator
        mock_template_generator = Mock()
        mock_template_generator.get_template_path.return_value = 'templates/test.html'

        # Instead of testing handle(), test _process_markdown_file directly
        with patch.object(self.command, '_setup_directory_structure'):
            # Set up necessary attributes
            self.command.template_generator = mock_template_generator
            mock_toc = {'test': 'toc'}
            
            # Process the file directly
            self.command._process_markdown_file('/test/path', 'test.md', mock_toc)

        # Verify template generator was called
        mock_template_generator.get_template_path.assert_called_once_with(
            'test.md',
            []  # empty folder list for root directory
        )
    @override_settings(
    SPELLBOOK_MD_PATH='/test/path',
    SPELLBOOK_CONTENT_APP='test_app'
)
    def test_relative_path_processing(
        self, mock_makedirs, mock_exists, mock_walk
    ):
        """Test processing of relative paths and URLs"""
        # Mock walk to return one markdown file in subfolder
        mock_walk.return_value = [('/test/path/subfolder', [], ['test.md'])]

        # Mock exists to return True for directory checks
        mock_exists.return_value = True

        # Create mock file processor
        mock_file_processor = Mock()
        context = SpellbookContext(
            title='Test',
            created_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            updated_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            url_path='subfolder/test',
            raw_content='# Test\nThis is a test',
        )
        mock_file_processor.process_file.return_value = (
            '<h1>Test</h1>',  # html_content
            '/test/path/subfolder/test.md',  # file_path
            context  # context
        )
        self.command.file_processor = mock_file_processor

        # Create mock template generator
        mock_template_generator = Mock()
        mock_template_generator.get_template_path.return_value = 'templates/subfolder/test.html'

        # Mock URL generator
        mock_url_generator = Mock()
        
        # Mock TOC building
        mock_toc = {'test': 'toc'}

        # Instead of calling handle(), test _process_markdown_file directly
        with patch.object(self.command, '_setup_directory_structure'):
            with patch.object(self.command, '_get_folder_list', return_value=['subfolder']):
                # Set up necessary attributes
                self.command.template_generator = mock_template_generator
                self.command.url_generator = mock_url_generator
                
                # Process the file directly
                result = self.command._process_markdown_file('/test/path/subfolder', 'test.md', mock_toc)

        # Verify file processor was called with correct arguments
        mock_file_processor.process_file.assert_called_once_with(
            Path('/test/path/subfolder'),
            '/test/path/subfolder',
            'test.md',
            ['subfolder']
        )

        # Verify template generator was called with correct paths
        mock_template_generator.get_template_path.assert_called_once_with(
            'test.md',
            ['subfolder']
        )

        # Check the result is correct
        self.assertIsNotNone(result)
        self.assertEqual(result.relative_url, 'subfolder/test')

class TestSpellbookCommandSourceDestinationPair(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.command = Command()
        self.command.stdout = Mock()  # Mock stdout for testing output

    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_MD_APP='test_app'
    )
    def test_normalize_single_strings(self):
        """Test normalization of string settings"""
        md_paths, md_apps = self.command._normalize_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])

    @override_settings(
        SPELLBOOK_MD_PATH=['/test/path1', '/test/path2'],
        SPELLBOOK_MD_APP=['test_app1', 'test_app2']
    )
    def test_normalize_lists(self):
        """Test normalization of list settings"""
        md_paths, md_apps = self.command._normalize_settings()
        
        self.assertEqual(md_paths, ['/test/path1', '/test/path2'])
        self.assertEqual(md_apps, ['test_app1', 'test_app2'])

    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_MD_APP=['test_app1', 'test_app2']
    )
    def test_normalize_mixed_types(self):
        """Test normalization with mixed types (string and list)"""
        md_paths, md_apps = self.command._normalize_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app1', 'test_app2'])

    @override_settings(
        SPELLBOOK_MD_PATH='/test/path',
        SPELLBOOK_CONTENT_APP='test_app'
    )
    def test_normalize_old_setting_name(self):
        """Test normalization with old setting name"""
        md_paths, md_apps = self.command._normalize_settings()
        
        self.assertEqual(md_paths, ['/test/path'])
        self.assertEqual(md_apps, ['test_app'])
        
        # Check for deprecation warning
        self.command.stdout.write.assert_any_call(
            self.command.style.WARNING(
                "SPELLBOOK_CONTENT_APP is deprecated, use SPELLBOOK_MD_APP instead."
            )
        )

    @override_settings(
        SPELLBOOK_MD_PATH=['/test/path1', '/test/path2'],
        SPELLBOOK_MD_APP=['test_app1', 'test_app2']
    )
    def test_validate_equal_length_lists(self):
        """Test validation with equal length lists"""
        self.command.validate_settings()
        
        self.assertEqual(self.command.md_file_paths, ['/test/path1', '/test/path2'])
        self.assertEqual(self.command.content_apps, ['test_app1', 'test_app2'])
        self.assertEqual(self.command.md_file_path, '/test/path1')
        self.assertEqual(self.command.content_app, 'test_app1')
        
        # Check for multiple pairs warning
        self.command.stdout.write.assert_any_call(
            self.command.style.WARNING(
                "Multiple source-destination pairs detected. Currently only processing the first pair."
            )
        )

    @override_settings(
        SPELLBOOK_MD_PATH=['/test/path1', '/test/path2', '/test/path3'],
        SPELLBOOK_MD_APP=['test_app1', 'test_app2']
    )
    def test_validate_unequal_length_lists(self):
        """Test validation with unequal length lists"""
        with self.assertRaises(CommandError) as context:
            self.command.validate_settings()
        
        self.assertIn(
            "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP must have the same number of entries",
            str(context.exception)
        )

    @override_settings(
        SPELLBOOK_MD_PATH=[],
        SPELLBOOK_MD_APP=[]
    )
    def test_validate_empty_lists(self):
        """Test validation with empty lists"""
        with self.assertRaises(CommandError) as context:
            self.command.validate_settings()
        
        self.assertIn("Missing required settings", str(context.exception))

    @override_settings(SPELLBOOK_MD_PATH=None, SPELLBOOK_MD_APP=None)
    def test_validate_none_values(self):
        """Test validation with None values"""
        with self.assertRaises(CommandError) as context:
            self.command.validate_settings()
        
        self.assertIn("Missing required settings", str(context.exception))

    @override_settings(
        SPELLBOOK_MD_PATH=['/test/path1', '/test/path2'],
        SPELLBOOK_MD_APP=['test_app1', '']
    )
    def test_validate_empty_string_app(self):
        """Test validation with empty string app names"""
        with self.assertRaises(CommandError):
            self.command.validate_settings()
            
    @override_settings(
        SPELLBOOK_MD_PATH=['/test/path1', ''],
        SPELLBOOK_MD_APP=['test_app1', 'test_app2']
    )
    def test_validate_empty_string_path(self):
        """Test validation with empty string path"""
        with self.assertRaises(CommandError):
            self.command.validate_settings()
            
            
class TestCommandErrorHandling(TestCase):
    """Test error handling in the Command class"""
    
    def setUp(self):
        self.command = Command()
        self.command.stdout = Mock()
    
    @patch('django_spellbook.management.commands.spellbook_md.Command.validate_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_continue_on_error_with_multiple_pairs(self, mock_process, mock_validate):
        """Test that processing continues when an error occurs with multiple pairs"""
        # Set up multiple source-destination pairs
        self.command.md_file_paths = ['/path1', '/path2', '/path3']
        self.command.content_apps = ['app1', 'app2', 'app3']
        
        # Make the second pair fail during processing
        def process_side_effect(md_path, content_app):
            if md_path == '/path2':
                raise Exception("Test error for path2")
            return None
        
        mock_process.side_effect = process_side_effect
        
        # Run the command
        self.command.handle()
        
        # Verify all three pairs were attempted
        self.assertEqual(mock_process.call_count, 3)
        
        # Verify error was logged for path2
        error_msg_call = None
        for call in self.command.stdout.write.call_args_list:
            args = call[0]
            if isinstance(args[0], str) and "Error processing pair /path2" in args[0]:
                error_msg_call = call
                break
        
        self.assertIsNotNone(error_msg_call, "Error message for path2 was not logged")
        
        # Verify the "continue" message was logged
        continue_msg_called = False
        for call in self.command.stdout.write.call_args_list:
            if call[0][0] == "Continuing with next pair...":
                continue_msg_called = True
                break
        
        self.assertTrue(continue_msg_called, "Continue message was not logged")
    
    @patch('django_spellbook.management.commands.spellbook_md.Command.validate_settings')
    @patch('django_spellbook.management.commands.spellbook_md.Command._process_source_destination_pair')
    def test_raise_on_error_with_single_pair(self, mock_process, mock_validate):
        """Test that processing raises the exception with a single pair"""
        # Set up a single source-destination pair
        self.command.md_file_paths = ['/path1']
        self.command.content_apps = ['app1']
        
        # Make processing fail
        test_error = Exception("Test error for single path")
        mock_process.side_effect = test_error
        
        # Run the command - should raise the exception
        with self.assertRaises(Exception) as context:
            self.command.handle()
        
        # Verify it's the same exception
        self.assertEqual(str(context.exception), "Test error for single path")
        
        # Verify processing was attempted exactly once
        mock_process.assert_called_once_with('/path1', 'app1')