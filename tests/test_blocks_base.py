import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.template.loader import render_to_string
from django_spellbook.blocks.base import BasicSpellBlock


class TestBasicSpellBlock(TestCase):
    def setUp(self):
        """Set up test cases with a basic block instance."""
        class TestBlock(BasicSpellBlock):
            name = 'test_block'
            template = 'test_template.html'
            required_kwargs = {'required_param'}
            optional_kwargs = {'optional_param'}

        self.BlockClass = TestBlock
        self.test_content = "# Test Header\nTest content"
        self.test_kwargs = {
            'required_param': 'test_required',
            'optional_param': 'test_optional'
        }

    def test_initialization(self):
        """Test block initialization with various parameters."""
        # Test with content and kwargs
        block = self.BlockClass(self.test_content, **self.test_kwargs)
        self.assertEqual(block.content, self.test_content)
        self.assertEqual(block.kwargs, self.test_kwargs)
        self.assertEqual(block.name, 'test_block')
        self.assertEqual(block.template, 'test_template.html')

        # Test initialization with no content
        block = self.BlockClass(**self.test_kwargs)
        self.assertIsNone(block.content)

        # Test initialization with no kwargs
        block = self.BlockClass(self.test_content)
        self.assertEqual(block.kwargs, {})

    def test_get_context(self):
        """Test context generation for template rendering."""
        block = self.BlockClass(self.test_content, **self.test_kwargs)
        context = block.get_context()

        # Check if processed content is in context
        self.assertIn('content', context)
        # Check if kwargs are in context
        self.assertEqual(context['required_param'], 'test_required')
        self.assertEqual(context['optional_param'], 'test_optional')

    @patch('markdown.markdown')
    def test_process_content(self, mock_markdown):
        """Test markdown content processing."""
        mock_markdown.return_value = '<h1>Test Header</h1>\n<p>Test content</p>'

        block = self.BlockClass(self.test_content)
        processed_content = block.process_content()

        # Verify markdown was called with correct parameters
        mock_markdown.assert_called_once_with(
            self.test_content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
            ]
        )

        self.assertEqual(
            processed_content,
            '<h1>Test Header</h1>\n<p>Test content</p>'
        )

    def test_render(self):
        """Test template rendering with context."""
        expected_output = '<div>Rendered content</div>'

        block = self.BlockClass(self.test_content, **self.test_kwargs)

        # Create a mock for process_content
        with patch.object(block, 'process_content', return_value='<p>Processed content</p>') as mock_process:
            # Create a mock for render_to_string
            with patch('django_spellbook.blocks.base.render_to_string', return_value=expected_output) as mock_render:
                rendered_content = block.render()

                # Verify process_content was called
                mock_process.assert_called_once()

                # Verify render_to_string was called with correct parameters
                mock_render.assert_called_once_with(
                    'test_template.html',
                    {
                        'content': '<p>Processed content</p>',
                        'required_param': 'test_required',
                        'optional_param': 'test_optional'
                    }
                )

                self.assertEqual(rendered_content, expected_output)

    def test_render_no_template(self):
        """Test rendering without a template raises ValueError."""
        class NoTemplateBlock(BasicSpellBlock):
            name = 'no_template_block'

        block = NoTemplateBlock(self.test_content)
        with self.assertRaises(ValueError) as context:
            block.render()

        self.assertIn('No template specified', str(context.exception))

    def test_inheritance(self):
        """Test proper inheritance and attribute override."""
        class CustomBlock(BasicSpellBlock):
            name = 'custom_block'
            template = 'custom_template.html'
            required_kwargs = {'custom_required'}
            optional_kwargs = {'custom_optional'}

        block = CustomBlock('content')
        self.assertEqual(block.name, 'custom_block')
        self.assertEqual(block.template, 'custom_template.html')
        self.assertEqual(block.required_kwargs, {'custom_required'})
        self.assertEqual(block.optional_kwargs, {'custom_optional'})

    def test_none_content_handling(self):
        """Test handling of None content."""
        block = self.BlockClass(None)
        processed_content = block.process_content()
        self.assertEqual(processed_content, '')

    @patch('markdown.markdown')
    def test_markdown_extensions(self, mock_markdown):
        """Test that markdown extensions are properly configured."""
        block = self.BlockClass(self.test_content)
        block.process_content()

        # Verify all required extensions are included
        _, kwargs = mock_markdown.call_args
        extensions = kwargs.get('extensions', [])
        required_extensions = [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
        ]
        for ext in required_extensions:
            self.assertIn(ext, extensions)
