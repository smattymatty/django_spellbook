import unittest
from unittest.mock import patch, Mock, MagicMock
import datetime
from pathlib import Path
from django.test import TestCase
from django.core.management.base import CommandError

from django_spellbook.markdown.context import SpellbookContext

class TestSpellbookContext(TestCase):
    """Tests for the SpellbookContext class."""
    
    def test_to_dict(self):
        """Test to_dict method."""
        context = SpellbookContext(
            title="Test Page",
            published="datetime.datetime(2023, 1, 1)",
            modified="datetime.datetime(2023, 2, 1)",
            url_path="test/page",
            raw_content="Test content",
            is_public=True,
            tags=["test", "example"],
            custom_meta={"key": "value"}
        )
        
        result = context.to_dict()
        
        # Verify other keys are converted
        self.assertIn('title', result)
        self.assertIn('published', result)
        self.assertIn('modified', result)
        self.assertIn('url_path', result)
        self.assertIn('raw_content', result)
        self.assertIn('is_public', result)
        self.assertIn('tags', result)
        self.assertIn('custom_meta', result)
        
    
        
class TestSpellBookErrors(TestCase):
    """Tests for error handling in the SpellbookContext class."""
    
    def test_to_dict_key_processing_exception(self):
        """Test exception during individual key processing."""
        context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content="Arbitrary Error String, Very Specific for Testing Purposes",
        )

        with self.assertRaises(RuntimeError):
            context.to_dict()
            
    def test_validate_missing_required_field(self):
        """Test validate method with missing required field."""
        context = SpellbookContext(
            title=None,
            url_path="test/page",
            raw_content="Test content",
            is_public=True,
            tags=["test", "example"],
            custom_meta={"key": "value"}
        )

        errors = context.validate()
        
        self.assertIn("Missing required field: title", errors[0])
        
    def test_prepare_metadata_missing_raw_content(self):
        """Test prepare_metadata method with missing raw_content."""
        context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content=None,
            is_public=True,
            tags=["test", "example"],
            custom_meta={"key": "value"}
        )
        
        with self.assertRaises(ValueError) as cm:
            context.prepare_metadata("test_app", "test/page")
            
        self.assertIn("Raw content is empty", str(cm.exception))
        
    def test_prepare_metadata_with_author(self):
        """Test prepare_metadata method includes author field."""
        context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content="Test content with some words",
            is_public=True,
            tags=["test", "example"],
            author="Jane Doe",
            custom_meta={"key": "value"}
        )
        
        metadata = context.prepare_metadata("test_app", "test/page")
        
        self.assertEqual(metadata['author'], "Jane Doe")
        self.assertIn('author', metadata)
        
    def test_prepare_metadata_without_author(self):
        """Test prepare_metadata method when author is None."""
        context = SpellbookContext(
            title="Test Page",
            published=datetime.datetime(2023, 1, 1),
            modified=datetime.datetime(2023, 2, 1),
            url_path="test/page",
            raw_content="Test content with some words",
            is_public=True,
            tags=["test", "example"],
            author=None,
            custom_meta={"key": "value"}
        )
        
        metadata = context.prepare_metadata("test_app", "test/page")
        
        self.assertIsNone(metadata['author'])
        self.assertIn('author', metadata)
        
