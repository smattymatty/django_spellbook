import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, date
from django_spellbook.markdown.frontmatter import FrontMatterParser, multi_bool
from django_spellbook.markdown.context import SpellbookContext
import tempfile
import os
from typing import Optional, List, Dict, Any

from django_spellbook.utils import titlefy


class TestFrontMatterParser(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(os.path.join(self.temp_dir, 'test.md'))
        self.temp_file.touch()

    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_parse_valid_frontmatter(self):
        """Test parsing valid front matter"""
        content = """---
title: Test Title
is_public: true
tags:
  - test
  - example
custom: value
---
Content here"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata['title'], 'Test Title')
        self.assertTrue(parser.metadata['is_public'])
        self.assertEqual(parser.metadata['tags'], ['test', 'example'])
        self.assertEqual(parser.metadata['custom'], 'value')
        self.assertEqual(parser.raw_content, 'Content here')

    def test_parse_invalid_frontmatter(self):
        """Test parsing invalid front matter"""
        content = """---
invalid: yaml:
  - unclosed list
---
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata, {})
        self.assertEqual(parser.raw_content, content)

    def test_no_frontmatter(self):
        """Test content without front matter"""
        content = "Just content"
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata, {})
        self.assertEqual(parser.raw_content, content)

    def test_incomplete_frontmatter(self):
        """Test incomplete front matter markers"""
        content = """---
title: Test
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata, {})
        self.assertEqual(parser.raw_content, content)

    def test_empty_frontmatter(self):
        """Test empty front matter"""
        content = """---
---
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata, {})
        self.assertEqual(parser.raw_content, 'Content')

    def test_non_dict_frontmatter(self):
        """Test front matter that doesn't evaluate to a dictionary"""
        content = """---
- just
- a
- list
---
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata, {})
        self.assertEqual(parser.raw_content, 'Content')

    def test_get_context(self):
        """Test context generation from front matter"""
        content = """---
title: Test Title
is_public: true
tags:
  - test
custom_field: value
---
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        context = parser.get_context('/test/url')

        self.assertIsInstance(context, SpellbookContext)
        self.assertEqual(context.title, 'Test Title')
        self.assertTrue(context.is_public)
        self.assertEqual(context.tags, ['test'])
        self.assertEqual(context.custom_meta, {'custom_field': 'value'})
        self.assertEqual(context.url_path, '/test/url')
        self.assertEqual(context.raw_content, 'Content')

    def test_default_values(self):
        """Test default values in context generation"""
        content = "Just content"
        parser = FrontMatterParser(content, self.temp_file)
        context = parser.get_context('/test/url')

        self.assertEqual(context.title, titlefy(self.temp_file.stem))
        self.assertTrue(context.is_public)
        self.assertEqual(context.tags, [])
        self.assertEqual(context.custom_meta, {})

    def test_unicode_handling(self):
        """Test handling of Unicode characters in front matter"""
        content = """---
title: 测试标题
tags: [测试, 示例]
---
Unicode content 内容"""
        parser = FrontMatterParser(content, self.temp_file)
        self.assertEqual(parser.metadata['title'], '测试标题')
        self.assertEqual(parser.metadata['tags'], ['测试', '示例'])
        self.assertEqual(parser.raw_content, 'Unicode content 内容')

    def test_dash_stripped_url_path(self):
        """Test URL path generation with dashes"""
        content = """---
title: Test Title
---
Content"""
        parser = FrontMatterParser(content, self.temp_file)
        context = parser.get_context('--test-url-path/--test-url-path-2')

        self.assertEqual(context.title, 'Test Title')
        self.assertEqual(context.url_path, 'test-url-path/test-url-path-2')


class TestMultiBool(unittest.TestCase):
    def test_string_values(self):
        """Test string boolean values"""
        self.assertFalse(multi_bool('false'))
        self.assertFalse(multi_bool('False'))
        self.assertFalse(multi_bool('f'))
        self.assertFalse(multi_bool('F'))
        self.assertFalse(multi_bool('no'))
        self.assertFalse(multi_bool('NO'))
        self.assertFalse(multi_bool('n'))
        self.assertFalse(multi_bool('N'))
        self.assertFalse(multi_bool('0'))

        self.assertTrue(multi_bool('true'))
        self.assertTrue(multi_bool('True'))
        self.assertTrue(multi_bool('t'))
        self.assertTrue(multi_bool('T'))
        self.assertTrue(multi_bool('yes'))
        self.assertTrue(multi_bool('YES'))
        self.assertTrue(multi_bool('y'))
        self.assertTrue(multi_bool('Y'))
        self.assertTrue(multi_bool('1'))

    def test_boolean_values(self):
        """Test boolean values"""
        self.assertFalse(multi_bool(False))
        self.assertTrue(multi_bool(True))

    def test_other_values(self):
        """Test other value types"""
        self.assertTrue(multi_bool(1))
        self.assertFalse(multi_bool(0))
        self.assertTrue(multi_bool([1]))  # Non-empty list is True
        self.assertFalse(multi_bool([]))  # Empty list is False
        self.assertTrue(multi_bool('other'))  # Other strings are True


class TestParseDateFromMetadata(unittest.TestCase):

    def setUp(self):
        """Set up a dummy parser instance for each test."""
        # Pass dummy content and path, as they aren't used by the method directly,
        # except self.file_path which is used in warnings.
        self.parser = FrontMatterParser("dummy content", Path("dummy_file.md"))
        # Reset metadata for each test
        self.parser.metadata = {}

    # --- Happy Path Tests ---

    def test_found_datetime_object(self):
        """Test finding a key with a datetime object value."""
        dt_obj = datetime(2024, 5, 15, 10, 30, 0)
        self.parser.metadata = {'published': dt_obj}
        result = self.parser._parse_date_from_metadata(['published'])
        self.assertEqual(result, dt_obj)

    def test_found_date_object(self):
        """Test finding a key with a date object value (should be converted)."""
        d_obj = date(2024, 5, 15)
        expected_dt = datetime(2024, 5, 15, 0, 0, 0) # Midnight time
        self.parser.metadata = {'event_date': d_obj}
        result = self.parser._parse_date_from_metadata(['event_date'])
        self.assertEqual(result, expected_dt)

    def test_found_iso_string_datetime(self):
        """Test finding a key with a valid ISO datetime string."""
        iso_str = "2024-03-10T15:45:30"
        expected_dt = datetime(2024, 3, 10, 15, 45, 30)
        self.parser.metadata = {'created_at': iso_str}
        result = self.parser._parse_date_from_metadata(['created_at'])
        self.assertEqual(result, expected_dt)

    def test_found_iso_string_date_only(self):
        """Test finding a key with a valid ISO date-only string."""
        iso_str = "2024-02-20"
        expected_dt = datetime(2024, 2, 20, 0, 0, 0)
        self.parser.metadata = {'date': iso_str}
        result = self.parser._parse_date_from_metadata(['date'])
        self.assertEqual(result, expected_dt)

    def test_found_iso_string_with_space(self):
        """Test finding a key with a valid ISO-like date string using space."""
        # Note: datetime.fromisoformat supports space separator as of Python 3.7+
        iso_str = "2024-03-10 15:45:30"
        expected_dt = datetime(2024, 3, 10, 15, 45, 30)
        self.parser.metadata = {'created_at': iso_str}
        result = self.parser._parse_date_from_metadata(['created_at'])
        self.assertEqual(result, expected_dt)

    def test_found_fallback_string_date_only(self):
        """Test finding a key with YYYY-MM-DD format (using strptime fallback)."""
        # This test relies on fromisoformat potentially failing and strptime succeeding.
        # However, fromisoformat often handles YYYY-MM-DD directly.
        # Let's ensure it works regardless of which parser handles it.
        date_str = "2023-12-25"
        expected_dt = datetime(2023, 12, 25, 0, 0, 0)
        self.parser.metadata = {'holiday': date_str}
        result = self.parser._parse_date_from_metadata(['holiday'])
        self.assertEqual(result, expected_dt)

    def test_string_with_whitespace(self):
        """Test parsing a valid date string with leading/trailing whitespace."""
        date_str = "  2024-01-01  "
        expected_dt = datetime(2024, 1, 1, 0, 0, 0)
        self.parser.metadata = {'new_year': date_str}
        result = self.parser._parse_date_from_metadata(['new_year'])
        self.assertEqual(result, expected_dt)

    def test_first_key_found(self):
        """Test using the first key when multiple valid keys are present."""
        dt_obj1 = datetime(2024, 1, 1)
        dt_obj2 = datetime(2024, 2, 2)
        self.parser.metadata = {'published': dt_obj1, 'date': dt_obj2}
        # 'published' comes before 'date' in the check list
        result = self.parser._parse_date_from_metadata(['published', 'date'])
        self.assertEqual(result, dt_obj1)

    def test_second_key_found(self):
        """Test using the second key when the first key is missing."""
        dt_obj2 = datetime(2024, 2, 2)
        self.parser.metadata = {'not_a_date_key': 'abc', 'date': dt_obj2}
        # 'published' is missing, 'date' should be found
        result = self.parser._parse_date_from_metadata(['published', 'date'])
        self.assertEqual(result, dt_obj2)

    def test_second_key_found_after_invalid(self):
        """Test using the second key when the first is present but invalid."""
        dt_obj2 = datetime(2024, 2, 2)
        self.parser.metadata = {'published': 'invalid-date-format', 'date': dt_obj2}
        # 'published' is invalid, 'date' should be found and used
        with patch('builtins.print') as mock_print: # Check warning for the invalid one
             result = self.parser._parse_date_from_metadata(['published', 'date'])
        self.assertEqual(result, dt_obj2)
        mock_print.assert_called_once() # Ensure the warning was printed for 'published'
        self.assertIn("Warning: Could not parse date string 'invalid-date-format' for key 'published'", mock_print.call_args[0][0])

    # --- Sad Path / Edge Case Tests ---

    def test_no_keys_provided(self):
        """Test with an empty list of keys to check."""
        self.parser.metadata = {'date': datetime.now()} # Metadata has a date
        result = self.parser._parse_date_from_metadata([]) # But no keys to check
        self.assertIsNone(result)

    def test_no_matching_keys_found(self):
        """Test when keys are provided but none exist in metadata."""
        self.parser.metadata = {'other_meta': 'value'}
        result = self.parser._parse_date_from_metadata(['published', 'date'])
        self.assertIsNone(result)

    def test_key_found_with_none_value(self):
        """Test when a key exists but its value is None."""
        self.parser.metadata = {'published': None}
        result = self.parser._parse_date_from_metadata(['published'])
        # The `if value:` check handles this, should return None
        self.assertIsNone(result)

    def test_key_found_with_empty_string_value(self):
        """Test when a key exists but its value is an empty string."""
        self.parser.metadata = {'published': ''}
        with patch('builtins.print') as mock_print:
             result = self.parser._parse_date_from_metadata(['published'])
        # The `if value:` check handles this, should return None
        self.assertIsNone(result)
        mock_print.assert_not_called() # Should not warn for empty string



    @patch('builtins.print') # Use decorator for patching print
    def test_invalid_string_format(self, mock_print):
        """Test an invalid/unsupported date string format."""
        self.parser.metadata = {'published': '15 May 2024'} # Unsupported format
        result = self.parser._parse_date_from_metadata(['published'])
        self.assertIsNone(result)
        # Check that a warning was printed
        mock_print.assert_called_once()
        self.assertIn("Warning: Could not parse date string '15 May 2024'", mock_print.call_args[0][0])
        self.assertIn("key 'published'", mock_print.call_args[0][0])

    @patch('builtins.print')
    def test_unexpected_type_integer(self, mock_print):
        """Test when the value is an integer."""
        self.parser.metadata = {'published': 20240515}
        result = self.parser._parse_date_from_metadata(['published'])
        self.assertIsNone(result)
        # Check that a warning for unexpected type was printed
        mock_print.assert_called_once()
        self.assertIn("Warning: Unexpected type '<class 'int'>'", mock_print.call_args[0][0])
        self.assertIn("key 'published'", mock_print.call_args[0][0])

    @patch('builtins.print')
    def test_unexpected_type_list(self, mock_print):
        """Test when the value is a list."""
        self.parser.metadata = {'published': [2024, 5, 15]}
        result = self.parser._parse_date_from_metadata(['published'])
        self.assertIsNone(result)
        # Check that a warning for unexpected type was printed
        mock_print.assert_called_once()
        self.assertIn("Warning: Unexpected type '<class 'list'>'", mock_print.call_args[0][0])
        self.assertIn("key 'published'", mock_print.call_args[0][0])


    @patch('builtins.print')
    def test_only_invalid_formats_present(self, mock_print):
        """Test when multiple keys exist but all have invalid formats."""
        self.parser.metadata = {
            'published': 'May 15, 2024',
            'date': '15/05/2024'
        }
        result = self.parser._parse_date_from_metadata(['published', 'date'])
        self.assertIsNone(result)
        # Check that warnings were printed for both attempts
        self.assertEqual(mock_print.call_count, 2)
        self.assertIn("Warning: Could not parse date string 'May 15, 2024'", mock_print.call_args_list[0][0][0])
        self.assertIn("Warning: Could not parse date string '15/05/2024'", mock_print.call_args_list[1][0][0])
