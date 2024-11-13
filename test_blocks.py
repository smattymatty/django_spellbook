from django.test import TestCase
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from unittest.mock import patch
import logging

from .markdown.parser import MarkdownParser
from .blocks import BasicSpellBlock, SpellBlockRegistry
from .blocks.exceptions import BlockRegistrationError

from bs4 import BeautifulSoup


class TestBlock(BasicSpellBlock):
    name = 'test'
    template = 'test_template.html'


class AnotherTestBlock(BasicSpellBlock):
    template = 'another_template.html'


class SpellBlockTests(TestCase):
    def setUp(self):
        # Clear registry before each test
        SpellBlockRegistry._registry = {}

    def test_basic_block_initialization(self):
        """Test basic block initialization with content and kwargs"""
        block = BasicSpellBlock(content="Test content", foo="bar")
        self.assertEqual(block.content, "Test content")
        self.assertEqual(block.kwargs, {"foo": "bar"})

    def test_block_registration(self):
        """Test block registration with decorator"""
        @SpellBlockRegistry.register()
        class MyBlock(BasicSpellBlock):
            name = 'my_block'
            template = 'test.html'

        self.assertIn('my_block', SpellBlockRegistry._registry)
        self.assertEqual(SpellBlockRegistry._registry['my_block'], MyBlock)

    def test_block_registration_with_name(self):
        """Test block registration with explicit name"""
        @SpellBlockRegistry.register('custom_name')
        class MyBlock(BasicSpellBlock):
            template = 'test.html'

        self.assertIn('custom_name', SpellBlockRegistry._registry)
        self.assertEqual(SpellBlockRegistry._registry['custom_name'], MyBlock)

    def test_duplicate_registration(self):
        """Test that registering duplicate block names raises an error"""
        @SpellBlockRegistry.register('duplicate')
        class Block1(BasicSpellBlock):
            template = 'test.html'

        with self.assertRaises(BlockRegistrationError):
            @SpellBlockRegistry.register('duplicate')
            class Block2(BasicSpellBlock):
                template = 'test.html'

    def test_invalid_block_registration(self):
        """Test that registering non-BasicSpellBlock class raises an error"""
        with self.assertRaises(BlockRegistrationError):
            @SpellBlockRegistry.register('invalid')
            class InvalidBlock:
                pass

    def test_missing_name_registration(self):
        """Test that registering block without name raises an error"""
        with self.assertRaises(BlockRegistrationError):
            @SpellBlockRegistry.register()
            class NoNameBlock(BasicSpellBlock):
                template = 'test.html'

    def test_block_content_processing(self):
        """Test markdown processing in block content"""
        block = BasicSpellBlock(content="**Bold** *Italic*")
        processed = block.process_content()
        self.assertIn("<strong>Bold</strong>", processed)
        self.assertIn("<em>Italic</em>", processed)

    def test_block_context_generation(self):
        """Test context generation for rendering"""
        block = BasicSpellBlock(content="Test", foo="bar")
        context = block.get_context()
        self.assertIn('content', context)
        self.assertEqual(context['foo'], 'bar')

    @patch('django_spellbook.blocks.base.render_to_string')
    def test_block_rendering(self, mock_render):
        """Test block rendering with template"""
        # Setup mock return value
        mock_render.return_value = "Rendered content"

        # Create and render block
        class RenderTestBlock(BasicSpellBlock):
            template = 'test_template.html'

        block = RenderTestBlock(content="Test content")
        rendered = block.render()

        # Assertions
        self.assertEqual(rendered, "Rendered content")
        mock_render.assert_called_once_with(
            'test_template.html',
            {'content': '<p>Test content</p>', }
        )

    def test_missing_template(self):
        """Test that rendering without template raises error"""
        block = BasicSpellBlock(content="Test")
        with self.assertRaises(ValueError):
            block.render()

    def test_get_nonexistent_block(self):
        """Test getting non-registered block returns None"""
        block = SpellBlockRegistry.get_block('nonexistent')
        self.assertIsNone(block)

    def test_required_kwargs(self):
        """Test block with required kwargs"""
        class RequiredKwargsBlock(BasicSpellBlock):
            template = 'test.html'
            required_kwargs = {'required_param'}

        block = RequiredKwargsBlock(content="Test")
        # Add test for required kwargs validation if implemented

    def test_optional_kwargs(self):
        """Test block with optional kwargs"""
        class OptionalKwargsBlock(BasicSpellBlock):
            template = 'test.html'
            optional_kwargs = {'optional_param'}

        block = OptionalKwargsBlock(content="Test")
        context = block.get_context()
        self.assertNotIn('optional_param', context)

        block = OptionalKwargsBlock(content="Test", optional_param="value")
        context = block.get_context()
        self.assertEqual(context['optional_param'], "value")


class DefaultBlocksTestCase(TestCase):
    def setUp(self):
        # Ensure blocks are registered
        from django_spellbook.spellblocks import AlertBlock, CardBlock
        self.alert_block = SpellBlockRegistry.get_block('alert')
        self.card_block = SpellBlockRegistry.get_block('card')

    def assertHtmlEqual(self, html1, html2):
        """Compare HTML strings semantically"""
        soup1 = BeautifulSoup(html1, 'html.parser')
        soup2 = BeautifulSoup(html2, 'html.parser')
        self.assertEqual(str(soup1), str(soup2))


class AlertBlockTests(DefaultBlocksTestCase):
    def test_alert_registration(self):
        """Test that AlertBlock is properly registered"""
        self.assertIsNotNone(self.alert_block)
        self.assertEqual(self.alert_block.name, 'alert')

    def test_alert_default_type(self):
        """Test alert with default type (info)"""
        block = self.alert_block(content="Test message")
        rendered = block.render()
        self.assertIn('spellbook-alert-info', rendered)
        self.assertIn('Test message', rendered)

    def test_alert_valid_types(self):
        """Test alert with all valid types"""
        valid_types = ['info', 'warning', 'success', 'danger']
        for alert_type in valid_types:
            block = self.alert_block(content="Test", type=alert_type)
            rendered = block.render()
            self.assertIn(f'spellbook-alert-{alert_type}', rendered)

    def test_alert_invalid_type(self):
        """Test alert with invalid type defaults to info"""
        block = self.alert_block(content="Test", type="invalid_type")
        rendered = block.render()
        self.assertIn('spellbook-alert-info', rendered)

    def test_alert_markdown_content(self):
        """Test that markdown content is properly rendered"""
        content = "**Bold** and *italic*"
        block = self.alert_block(content=content)
        rendered = block.render()
        self.assertIn('<strong>Bold</strong>', rendered)
        self.assertIn('<em>italic</em>', rendered)


class CardBlockTests(DefaultBlocksTestCase):
    def test_basic_card(self):
        """Test basic card without title or footer"""
        block = self.card_block(content="Test content")
        rendered = block.render()

        # Parse HTML to ignore CSS
        soup = BeautifulSoup(rendered, 'html.parser')
        card_div = soup.find('div', class_='spellbook-card')

        # Check that header is not present
        self.assertIsNone(card_div.find('div', class_='spellbook-card-header'))
        # Check that footer is not present
        self.assertIsNone(card_div.find('div', class_='spellbook-card-footer'))
        # Check content
        self.assertIn('Test content', card_div.find(
            'div', class_='spellbook-card-body').text)

    def test_card_with_markdown_content(self):
        """Test that markdown content is properly rendered in card"""
        content = """
# Header
- List item 1
- List item 2
        """
        block = self.card_block(content=content)
        rendered = block.render()

        # Parse HTML
        soup = BeautifulSoup(rendered, 'html.parser')
        card_body = soup.find('div', class_='spellbook-card-body')

        # Check markdown rendering
        self.assertIsNotNone(card_body.find('h1'))
        self.assertEqual(card_body.find('h1').text, 'Header')

        # Check list items
        list_items = card_body.find_all('li')
        self.assertEqual(len(list_items), 2)
        self.assertEqual(list_items[0].text, 'List item 1')
        self.assertEqual(list_items[1].text, 'List item 2')


class BlockParserTests(DefaultBlocksTestCase):
    def setUp(self):
        super().setUp()
        # Set up logging capture
        self.log_capture = []
        self.handler = logging.Handler()
        self.handler.emit = lambda record: self.log_capture.append(
            record.getMessage())
        logger = logging.getLogger('django_spellbook.blocks.registry')
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)

    def tearDown(self):
        # Clean up logging handler
        logger = logging.getLogger('django_spellbook.blocks.registry')
        logger.removeHandler(self.handler)
        super().tearDown()


def test_block_error_handling(self):
    """Test error handling in block parsing"""
    invalid_content = """Regular content

{~ nonexistent_block ~}
Test content
{~~}"""
    parser = MarkdownParser(invalid_content)
    rendered = parser.get_html()

    # Verify error message is in output
    self.assertIn("<!-- Block 'nonexistent_block' not found -->", rendered)

    # Verify regular content is preserved
    self.assertIn('Regular content', rendered)

    # Verify error was logged
    self.assertTrue(any(
        "Block 'nonexistent_block' not found in registry" in msg
        for msg in self.log_capture
    ))


class BlockRegistryTests(TestCase):
    def test_duplicate_registration(self):
        """Test that duplicate block registration raises error"""
        from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry

        @SpellBlockRegistry.register()
        class TestBlock(BasicSpellBlock):
            name = 'test_block'
            template = 'test.html'

        # Attempting to register another block with same name
        with self.assertRaises(Exception):
            @SpellBlockRegistry.register()
            class AnotherBlock(BasicSpellBlock):
                name = 'test_block'
                template = 'test.html'

    def test_block_without_name(self):
        """Test that block registration without name raises error"""
        from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry

        with self.assertRaises(Exception):
            @SpellBlockRegistry.register()
            class NoNameBlock(BasicSpellBlock):
                template = 'test.html'
