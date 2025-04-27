import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.template.loader import render_to_string
from django_spellbook.blocks import BasicSpellBlock

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter
from io import StringIO



class TestQuoteBlock(TestCase):
    def setUp(self):
        """Set up test cases with a QuoteBlock instance."""
        from django_spellbook.spellblocks import QuoteBlock
        self.BlockClass = QuoteBlock
        self.test_content = "This is a quote"
        self.test_kwargs = {
            'author': 'Test Author',
            'source': 'Test Source',
            'image': '/static/images/profile.jpg',
            'class': 'custom-class'
        }

    def test_initialization(self):
        """Test block initialization with various parameters."""
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)
        self.assertEqual(block.content, self.test_content)
        self.assertEqual(block.kwargs, self.test_kwargs)
        self.assertEqual(block.name, 'quote')
        self.assertEqual(block.template, 'django_spellbook/blocks/quote.html')

    def test_get_context(self):
        """Test context generation for template rendering."""
        # First update QuoteBlock to include the image parameter
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)
        context = block.get_context()

        # Check if all expected parameters are in context
        self.assertIn('content', context)
        self.assertEqual(context['author'], 'Test Author')
        self.assertEqual(context['source'], 'Test Source')
        self.assertEqual(context['image'], '/static/images/profile.jpg')
        self.assertEqual(context['class'], 'custom-class')

    def test_render(self):
        """Test template rendering with context."""
        expected_output = '<blockquote>Rendered quote with image</blockquote>'
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)

        # Create mocks for process_content and render_to_string
        with patch.object(block, 'process_content', return_value='<p>This is a quote</p>') as mock_process:
            with patch('django_spellbook.blocks.base.render_to_string', return_value=expected_output) as mock_render:
                rendered_content = block.render()

                # Verify process_content was called
                mock_process.assert_called_once()

                # Verify render_to_string was called with correct parameters
                mock_render.assert_called_once_with(
                    'django_spellbook/blocks/quote.html',
                    {
                        'content': '<p>This is a quote</p>',
                        'author': 'Test Author',
                        'source': 'Test Source',
                        'image': '/static/images/profile.jpg',
                        'class': 'custom-class'
                    }
                )

                self.assertEqual(rendered_content, expected_output)

    def test_render_without_image(self):
        """Test rendering without an image."""
        expected_output = '<blockquote>Rendered quote without image</blockquote>'

        # Create block without image
        kwargs_without_image = {k: v for k, v in self.test_kwargs.items() if k != 'image'}
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **kwargs_without_image)

        # Create mocks for process_content and render_to_string
        with patch.object(block, 'process_content', return_value='<p>This is a quote</p>') as mock_process:
            with patch('django_spellbook.blocks.base.render_to_string', return_value=expected_output) as mock_render:
                rendered_content = block.render()

                # Verify render_to_string was called without image parameter
                context = mock_render.call_args[0][1]
                self.assertEqual(context.get('image', ''), '')

                self.assertEqual(rendered_content, expected_output)

    def test_default_values(self):
        """Test that default values are provided when kwargs are missing."""
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content)
        context = block.get_context()
        
        self.assertEqual(context['author'], '')
        self.assertEqual(context['source'], '')
        self.assertEqual(context['class'], '')
        self.assertEqual(context.get('image', ''), '')


class TestPracticeBlock(TestCase):
    def setUp(self):
        """Set up test cases with a PracticeBlock instance."""
        from django_spellbook.spellblocks import PracticeBlock
        self.BlockClass = PracticeBlock
        self.test_content = "Practice steps\n1. Step one\n2. Step two"
        self.test_kwargs = {
            'difficulty': 'Advanced',
            'timeframe': '60 minutes',
            'impact': 'High',
            'focus': 'Productivity',
            'class': 'custom-class'
        }

    def test_initialization(self):
        """Test block initialization with various parameters."""
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)
        self.assertEqual(block.content, self.test_content)
        self.assertEqual(block.kwargs, self.test_kwargs)
        self.assertEqual(block.name, 'practice')
        self.assertEqual(block.template, 'django_spellbook/blocks/practice.html')

    def test_get_context(self):
        """Test context generation for template rendering."""
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)
        context = block.get_context()

        # Check if all expected parameters are in context
        self.assertIn('content', context)
        self.assertEqual(context['difficulty'], 'Advanced')
        self.assertEqual(context['timeframe'], '60 minutes')
        self.assertEqual(context['impact'], 'High')
        self.assertEqual(context['focus'], 'Productivity')
        self.assertEqual(context['class'], 'custom-class')

    def test_render(self):
        """Test template rendering with context."""
        expected_output = '<div class="practice-block">Rendered practice</div>'
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content, **self.test_kwargs)

        # Create mocks for process_content and render_to_string
        with patch.object(block, 'process_content', return_value='<p>Practice steps</p><ol><li>Step one</li><li>Step two</li></ol>') as mock_process:
            with patch('django_spellbook.blocks.base.render_to_string', return_value=expected_output) as mock_render:
                rendered_content = block.render()

                # Verify render_to_string was called with correct parameters
                mock_render.assert_called_once_with(
                    'django_spellbook/blocks/practice.html',
                    {
                        'content': '<p>Practice steps</p><ol><li>Step one</li><li>Step two</li></ol>',
                        'difficulty': 'Advanced',
                        'timeframe': '60 minutes',
                        'impact': 'High',
                        'focus': 'Productivity',
                        'class': 'custom-class'
                    }
                )

                self.assertEqual(rendered_content, expected_output)

    def test_default_values(self):
        """Test that default values are provided when kwargs are missing."""
        block = self.BlockClass(MarkdownReporter(StringIO()), self.test_content)
        context = block.get_context()
        
        self.assertEqual(context['difficulty'], 'Moderate')
        self.assertEqual(context['timeframe'], 'Varies')
        self.assertEqual(context['impact'], 'Medium')
        self.assertEqual(context['focus'], 'General')
        self.assertEqual(context['class'], '')