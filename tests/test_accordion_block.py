import unittest
from unittest.mock import Mock, patch
from django.template.loader import select_template
from django.template.exceptions import TemplateDoesNotExist

from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry
from django_spellbook.spellblocks import AccordionBlock


class TestAccordionBlock(unittest.TestCase):
    """Test cases for the AccordionBlock class."""

    def setUp(self):
        """Set up test environment."""
        self.reporter = Mock()
        self.reporter.record_spellblock_usage = Mock()

    def test_initialization(self):
        """Test basic initialization of AccordionBlock."""
        block = AccordionBlock(
            reporter=self.reporter,
            content="Test content",
            title="Test Title"
        )
        
        self.assertEqual(block.name, 'accordion')
        self.assertEqual(block.template, 'django_spellbook/blocks/accordion.html')
        self.assertEqual(block.content, "Test content")
        self.assertEqual(block.kwargs.get('title'), "Test Title")

    def test_get_context(self):
        """Test that get_context adds the required context variables."""
        block = AccordionBlock(
            reporter=self.reporter,
            content="Test content",
            title="Test Title",
            open=True
        )
        
        context = block.get_context()
        
        # Test that our context contains the expected values
        self.assertIn('content', context)
        self.assertIn('title', context)
        self.assertIn('open', context)
        self.assertEqual(context['title'], "Test Title")
        self.assertTrue(context['open'])

    def test_default_open_value(self):
        """Test that the 'open' parameter defaults to False if not provided."""
        block = AccordionBlock(
            reporter=self.reporter,
            content="Test content",
            title="Test Title"
        )
        
        context = block.get_context()
        self.assertFalse(context['open'])

if __name__ == '__main__':
    unittest.main()