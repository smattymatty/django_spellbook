import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from django_spellbook.blocks.base import BasicSpellBlock
from django_spellbook.blocks.registry import SpellBlockRegistry
from django_spellbook.blocks.exceptions import BlockRegistrationError


class TestSpellBlockRegistry(TestCase):
    def setUp(self):
        """Reset registry before each test."""
        SpellBlockRegistry._registry = {}

        # Create a basic valid block class for testing
        class ValidBlock(BasicSpellBlock):
            name = 'valid_block'
            template = 'test_template.html'

        self.ValidBlock = ValidBlock

    def test_valid_registration(self):
        """Test successful block registration."""
        # Test registration with class name
        @SpellBlockRegistry.register()
        class TestBlock(BasicSpellBlock):
            name = 'test_block'
            template = 'test.html'

        self.assertIn('test_block', SpellBlockRegistry._registry)
        self.assertEqual(SpellBlockRegistry._registry['test_block'], TestBlock)

        # Test registration with custom name
        @SpellBlockRegistry.register(name='custom_name')
        class AnotherBlock(BasicSpellBlock):
            template = 'another.html'

        self.assertIn('custom_name', SpellBlockRegistry._registry)
        self.assertEqual(
            SpellBlockRegistry._registry['custom_name'], AnotherBlock)

    def test_invalid_inheritance(self):
        """Test registration with invalid class inheritance."""
        with self.assertRaises(BlockRegistrationError) as context:
            @SpellBlockRegistry.register()
            class InvalidBlock:  # Does not inherit from BasicSpellBlock
                name = 'invalid_block'

        self.assertIn('must inherit from BasicSpellBlock',
                      str(context.exception))

    def test_missing_name(self):
        """Test registration with missing block name."""
        with self.assertRaises(BlockRegistrationError) as context:
            @SpellBlockRegistry.register()
            class NoNameBlock(BasicSpellBlock):
                template = 'test.html'

        self.assertIn('must have a name', str(context.exception))

    def test_duplicate_name(self):
        """Test registration with duplicate block names."""
        # Register first block
        @SpellBlockRegistry.register()
        class FirstBlock(BasicSpellBlock):
            name = 'duplicate_name'
            template = 'first.html'

        # Try to register second block with same name
        with self.assertRaises(BlockRegistrationError) as context:
            @SpellBlockRegistry.register()
            class SecondBlock(BasicSpellBlock):
                name = 'duplicate_name'
                template = 'second.html'

        self.assertIn('Multiple blocks registered', str(context.exception))

    def test_get_block(self):
        """Test retrieving registered blocks."""
        # Register a block
        @SpellBlockRegistry.register()
        class TestBlock(BasicSpellBlock):
            name = 'test_block'
            template = 'test.html'

        # Test getting existing block
        block_class = SpellBlockRegistry.get_block('test_block')
        self.assertEqual(block_class, TestBlock)

        # Test getting non-existent block
        block_class = SpellBlockRegistry.get_block('non_existent')
        self.assertIsNone(block_class)

    @patch('django_spellbook.blocks.registry.logger')
    def test_registration_logging(self, mock_logger):
        """Test logging during block registration."""
        # Test successful registration logging
        @SpellBlockRegistry.register()
        class TestBlock(BasicSpellBlock):
            name = 'test_block'
            template = 'test.html'

        mock_logger.debug.assert_called_with(
            "Successfully registered block: test_block")

        # Test error logging
        mock_logger.reset_mock()
        with self.assertRaises(BlockRegistrationError):
            @SpellBlockRegistry.register()
            class InvalidBlock:
                name = 'invalid_block'

        mock_logger.error.assert_called_once()

    def test_registration_with_custom_name_override(self):
        """Test registration with custom name overriding class name."""
        @SpellBlockRegistry.register(name='custom_override')
        class TestBlock(BasicSpellBlock):
            name = 'original_name'
            template = 'test.html'

        self.assertIn('custom_override', SpellBlockRegistry._registry)
        self.assertNotIn('original_name', SpellBlockRegistry._registry)

    def test_registration_error_handling(self):
        """Test general error handling during registration."""
        with patch('django_spellbook.blocks.registry.logger') as mock_logger:
            with self.assertRaises(BlockRegistrationError):
                @SpellBlockRegistry.register()
                class ErrorBlock(BasicSpellBlock):
                    name = None  # This will cause an error
                    template = 'test.html'

            mock_logger.error.assert_called_once()
