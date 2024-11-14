import unittest
import datetime
from unittest.mock import patch, Mock, mock_open, call
from pathlib import Path
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django_spellbook.management.commands.spellbook_md import Command
from django_spellbook.markdown.context import SpellbookContext


@override_settings(
    SPELLBOOK_MD_PATH='/test/path',
    SPELLBOOK_CONTENT_APP='test_app'
)
class TestSpellbookCommand(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.command = Command()
        self.command.stdout = Mock()  # Mock stdout for testing output

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
            toc = self.command._build_toc()

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

            # Call the method
            self.command._setup_directory_structure('/test/path/content')

            # Verify content_dir_path was set
            self.assertEqual(
                self.command.content_dir_path,
                '/test/path/test_app'
            )

            # Verify template directory was created
            expected_template_path = '/test/path/test_app/templates/test_app/spellbook_md'
            mock_makedirs.assert_called_once_with(expected_template_path)

            # Verify the template_dir was set
            self.assertEqual(
                self.command.template_dir,
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
                toc = self.command._build_toc()
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
        """Test successful processing of markdown files"""
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
        self.command.template_generator = mock_template_generator

        # Create mock URL generator
        mock_url_generator = Mock()
        self.command.url_generator = mock_url_generator

        # Mock TOC building
        mock_toc = {'test': 'toc'}

        # Mock the _setup_directory_structure method
        with patch.object(self.command, '_setup_directory_structure') as mock_setup:
            with patch.object(self.command, '_build_toc', return_value=mock_toc):
                # Call handle directly
                self.command.handle()

        # Verify file processor was called with correct arguments
        mock_file_processor.process_file.assert_called_once_with(
            Path('/test/path'),
            '/test/path',
            'test.md',
            []  # empty folder list for root directory
        )

        # Verify template generator was called
        mock_template_generator.get_template_path.assert_called_once_with(
            'test.md',
            []  # empty folder list for root directory
        )
        mock_template_generator.create_template.assert_called_once_with(
            'templates/test.html',
            '<h1>Test</h1>'
        )

        # Verify URL generator was called with correct arguments
        mock_url_generator.generate_urls_and_views.assert_called_once()
        call_args = mock_url_generator.generate_urls_and_views.call_args
        processed_files, passed_toc = call_args[0]

        self.assertEqual(len(processed_files), 1)
        self.assertEqual(processed_files[0].html_content, '<h1>Test</h1>')
        self.assertEqual(processed_files[0].relative_url, 'test')
        self.assertEqual(passed_toc, mock_toc)

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
        self.command.template_generator = mock_template_generator

        # Create mock URL generator
        mock_url_generator = Mock()
        self.command.url_generator = mock_url_generator

        # Mock TOC building
        mock_toc = {'test': 'toc'}

        # Mock the _setup_directory_structure method
        with patch.object(self.command, '_setup_directory_structure') as mock_setup:
            with patch.object(self.command, '_build_toc', return_value=mock_toc):
                # Call handle directly
                self.command.handle()

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

        # Verify URL generator was called with processed files
        mock_url_generator.generate_urls_and_views.assert_called_once()
        processed_files = mock_url_generator.generate_urls_and_views.call_args[0][0]
        self.assertEqual(len(processed_files), 1)
        self.assertEqual(processed_files[0].relative_url, 'subfolder/test')
