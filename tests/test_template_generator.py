import unittest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from django.core.management.base import CommandError
from django.test import override_settings
from django_spellbook.management.commands.processing.template_generator import TemplateGenerator


class TestTemplateGenerator(unittest.TestCase):
    def setUp(self):
        self.template_generator = TemplateGenerator(
            content_app='test_app',
            template_dir='/test/templates',
            base_template='custom_base.html'  # Now passed directly to constructor
        )

    def test_init(self):
        """Test TemplateGenerator initialization."""
        self.assertEqual(self.template_generator.content_app, 'test_app')
        self.assertEqual(self.template_generator.template_dir, '/test/templates')
        self.assertEqual(self.template_generator.base_template, 'custom_base.html')
        
        # Test initialization with None base_template
        generator_no_base = TemplateGenerator(
            content_app='test_app',
            template_dir='/test/templates',
            base_template=None
        )
        self.assertIsNone(generator_no_base.base_template)

    @patch('pathlib.Path.mkdir')
    def test_ensure_template_directory(self, mock_mkdir):
        """Test template directory creation."""
        template_path = Path('/test/templates/test.html')
        self.template_generator._ensure_template_directory(template_path)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_prepare_template_content_with_base(self):
        """Test template content preparation with base template."""
        html_content = "<h1>Test</h1>"
        result = self.template_generator._prepare_template_content(html_content)

        expected = (
            "{% extends 'custom_base.html' %}\n\n"
            "{% block spellbook_md %}\n"
            "<h1>Test</h1>\n"
            "{% endblock %}"
        )
        self.assertEqual(result, expected)

    def test_prepare_template_content_without_base(self):
        """Test template content preparation without base template."""
        generator_no_base = TemplateGenerator(
            content_app='test_app',
            template_dir='/test/templates',
            base_template=None
        )
        html_content = "<h1>Test</h1>"
        result = generator_no_base._prepare_template_content(html_content)
        self.assertEqual(result, html_content)

    def test_get_template_path(self):
        """Test template path calculation."""
        filename = "test.md"
        folders = ["folder1", "folder2"]

        expected_path = Path('/test/templates/folder2/folder1/test.html')
        result = self.template_generator.get_template_path(filename, folders)

        self.assertEqual(result, expected_path)

    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.mkdir')
    def test_create_template_success(self, mock_mkdir, mock_write):
        """Test successful template creation."""
        template_path = Path('/test/templates/test.html')
        html_content = "<h1>Test</h1>"

        self.template_generator.create_template(template_path, html_content)

        mock_mkdir.assert_called_once()
        mock_write.assert_called_once()

    @patch('pathlib.Path.write_text')
    def test_create_template_error(self, mock_write):
        """Test template creation with error."""
        mock_write.side_effect = IOError("Write error")
        template_path = Path('/test/templates/test.html')
        html_content = "<h1>Test</h1>"

        with self.assertRaises(CommandError) as context:
            self.template_generator.create_template(template_path, html_content)

        self.assertIn("Could not create template", str(context.exception))

    def test_build_folder_path(self):
        """Test folder path building."""
        folders = ["folder1", "folder2", "folder3"]
        result = self.template_generator._build_folder_path(folders)
        expected = Path("folder3/folder2/folder1")
        self.assertEqual(result, expected)

    def test_convert_filename(self):
        """Test filename conversion from markdown to HTML."""
        filename = "test.md"
        result = self.template_generator._convert_filename(filename)
        self.assertEqual(result, "test.html")

    def test_get_base_template(self):
        """Test getting base template name from the instance variable."""
        base_template = self.template_generator._get_base_template()
        self.assertEqual(base_template, 'custom_base.html')
        
        # Test with None
        generator_no_base = TemplateGenerator(
            content_app='test_app',
            template_dir='/test/templates',
            base_template=None
        )
        self.assertIsNone(generator_no_base._get_base_template())

    def test_wrap_with_base_template(self):
        """Test wrapping content with base template."""
        html_content = "<h1>Test</h1>"
        result = self.template_generator._wrap_with_base_template(html_content, 'base.html')
        
        expected = (
            "{% extends 'base.html' %}\n\n"
            "{% block spellbook_md %}\n"
            "<h1>Test</h1>\n"
            "{% endblock %}"
        )
        self.assertEqual(result, expected)