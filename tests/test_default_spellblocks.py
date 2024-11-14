import unittest
from unittest.mock import patch, Mock
from django.test import TestCase  # Use Django's TestCase
from django.template.loader import get_template
from django_spellbook.spellblocks import AlertBlock, CardBlock


class TestAlertBlock(TestCase):  # Change to Django's TestCase
    def setUp(self):
        self.alert_block = AlertBlock()

    def test_initialization(self):
        """Test basic initialization of AlertBlock"""
        block = AlertBlock(content="Test content")
        self.assertEqual(block.name, 'alert')
        self.assertEqual(block.template, 'django_spellbook/blocks/alert.html')
        self.assertEqual(block.content, "Test content")

    def test_valid_alert_types(self):
        """Test all valid alert types"""
        for alert_type in AlertBlock.VALID_TYPES:
            with self.subTest(alert_type=alert_type):
                block = AlertBlock(type=alert_type)
                context = block.get_context()
                self.assertEqual(context['type'], alert_type)

    def test_invalid_alert_type(self):
        """Test invalid alert type defaults to 'info'"""
        with patch('builtins.print') as mock_print:
            block = AlertBlock(type='invalid')
            context = block.get_context()

            self.assertEqual(context['type'], 'info')
            mock_print.assert_called_once()
            warning_msg = mock_print.call_args[0][0]
            self.assertIn("Invalid alert type 'invalid'", warning_msg)
            self.assertIn("Valid types are:", warning_msg)

    def test_alert_with_content(self):
        """Test alert with markdown content"""
        content = "**Bold** and *italic*"
        block = AlertBlock(content=content)
        context = block.get_context()

        self.assertIn("<strong>Bold</strong>", context['content'])
        self.assertIn("<em>italic</em>", context['content'])
        self.assertEqual(context['type'], 'info')  # default type

    # Patch at the correct location
    @patch('django_spellbook.blocks.base.render_to_string')
    def test_alert_rendering(self, mock_render):
        """Test alert template rendering"""
        mock_render.return_value = "<div>Rendered content</div>"

        block = AlertBlock(
            content="Test content",
            type="warning"
        )
        result = block.render()

        mock_render.assert_called_once_with(
            'django_spellbook/blocks/alert.html',
            {
                'content': '<p>Test content</p>',
                'type': 'warning'
            }
        )
        self.assertEqual(result, "<div>Rendered content</div>")


class TestCardBlock(TestCase):  # Change to Django's TestCase
    def setUp(self):
        self.card_block = CardBlock()

    def test_initialization(self):
        """Test basic initialization of CardBlock"""
        block = CardBlock(content="Test content")
        self.assertEqual(block.name, 'card')
        self.assertEqual(block.template, 'django_spellbook/blocks/card.html')
        self.assertEqual(block.content, "Test content")

    def test_card_with_all_options(self):
        """Test card with all optional elements"""
        block = CardBlock(
            content="Card content",
            title="Test Title",
            footer="Test Footer",
            class_="custom-class"  # Note the underscore
        )
        context = block.get_context()

        self.assertEqual(context['title'], "Test Title")
        self.assertEqual(context['footer'], "Test Footer")
        # Note: no underscore in context
        self.assertEqual(context['class_'], "custom-class")
        self.assertIn("<p>Card content</p>", context['content'])

    def test_card_without_optional_elements(self):
        """Test card without optional elements"""
        block = CardBlock(content="Just content")
        context = block.get_context()

        self.assertIsNone(context.get('title'))
        self.assertIsNone(context.get('footer'))
        self.assertEqual(context.get('class', ''), '')
        self.assertIn("<p>Just content</p>", context['content'])

    def test_card_with_markdown_content(self):
        """Test card with markdown content processing"""
        content = "# Heading\n\n- List item 1\n- List item 2"
        block = CardBlock(content=content)
        context = block.get_context()

        self.assertIn("<h1>Heading</h1>", context['content'])
        self.assertIn("<li>List item 1</li>", context['content'])
        self.assertIn("<li>List item 2</li>", context['content'])

    # Patch at the correct location
    @patch('django_spellbook.blocks.base.render_to_string')
    def test_card_rendering(self, mock_render):
        """Test card template rendering"""
        mock_render.return_value = "<div>Rendered card</div>"

        block = CardBlock(
            content="Test content",
            title="Test Title",
            footer="Test Footer",
            class_="custom-class"
        )
        result = block.render()

        mock_render.assert_called_once_with(
            'django_spellbook/blocks/card.html',
            {
                'content': '<p>Test content</p>',
                'title': 'Test Title',
                'footer': 'Test Footer',
                'class_': 'custom-class',
                'class': ''
            }
        )
        self.assertEqual(result, "<div>Rendered card</div>")

    def test_empty_card(self):
        """Test card with no content or options"""
        block = CardBlock()
        context = block.get_context()

        self.assertEqual(context['content'], '')
        self.assertIsNone(context.get('title'))
        self.assertIsNone(context.get('footer'))
        self.assertEqual(context.get('class', ''), '')
