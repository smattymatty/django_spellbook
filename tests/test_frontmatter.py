import unittest
from pathlib import Path
from datetime import datetime
from django_spellbook.markdown.frontmatter import FrontMatterParser, multi_bool
from django_spellbook.markdown.context import SpellbookContext
import tempfile
import os


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

        self.assertEqual(context.title, self.temp_file.stem)
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
