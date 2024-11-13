import os
import yaml
from pathlib import Path
from datetime import datetime
from django.test import TestCase
from django.conf import settings
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.markdown.toc import TOCGenerator, TOCEntry


class BasicContextTests(TestCase):
    """Test basic SpellbookContext functionality"""

    def setUp(self):
        self.context = SpellbookContext(
            title="Test Page",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            url_path="test/page",
            raw_content="# Test\nContent here",
        )

    def test_default_values(self):
        """Test default values are set correctly"""
        self.assertTrue(self.context.is_public)
        self.assertEqual(self.context.tags, [])
        self.assertEqual(self.context.custom_meta, {})
        self.assertEqual(self.context.toc, {})
        self.assertIsNone(self.context.next_page)
        self.assertIsNone(self.context.prev_page)

    def test_required_fields(self):
        """Test all required fields are present"""
        self.assertEqual(self.context.title, "Test Page")
        self.assertIsInstance(self.context.created_at, datetime)
        self.assertIsInstance(self.context.updated_at, datetime)
        self.assertEqual(self.context.url_path, "test/page")
        self.assertEqual(self.context.raw_content, "# Test\nContent here")


class BasicFrontMatterTests(TestCase):
    """Test FrontMatter parsing and context generation"""

    def setUp(self):
        # Create a temporary test directory and file
        self.test_dir = Path("test_files")
        self.test_dir.mkdir(exist_ok=True)

        self.test_file = self.test_dir / "test.md"
        self.basic_content = """---
title: Test Title
tags: ['python', 'django']
custom_field: value
---
# Content here
"""
        # Actually create the test file
        self.test_file.write_text(self.basic_content)

        self.parser = FrontMatterParser(self.basic_content, self.test_file)

    def tearDown(self):
        # Clean up test files
        if self.test_file.exists():
            self.test_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()

    def test_basic_frontmatter_parsing(self):
        """Test basic frontmatter is parsed correctly"""
        self.assertEqual(self.parser.metadata['title'], "Test Title")
        self.assertEqual(self.parser.metadata['tags'], ['python', 'django'])
        self.assertEqual(self.parser.metadata['custom_field'], 'value')
        self.assertEqual(self.parser.raw_content.strip(), "# Content here")

    def test_context_generation(self):
        """Test context is generated correctly from frontmatter"""
        context = self.parser.get_context("test")
        self.assertEqual(context.title, "Test Title")
        self.assertEqual(context.tags, ['python', 'django'])
        self.assertEqual(context.custom_meta['custom_field'], 'value')

    def test_missing_frontmatter(self):
        """Test handling of content without frontmatter"""
        content = "# Just content\nNo frontmatter"
        # Create a new test file for this test
        test_file = self.test_dir / "no_frontmatter.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        # Clean up
        test_file.unlink()

        # Should default to filename
        self.assertEqual(context.title, "no_frontmatter")
        self.assertEqual(context.raw_content, content)


class BasicTOCTests(TestCase):
    """Test Table of Contents generation"""

    def setUp(self):
        self.toc_generator = TOCGenerator()

    def test_root_level_entry(self):
        """Test adding a root-level entry"""
        self.toc_generator.add_entry(
            Path("introduction.md"),
            "Introduction",
            "introduction"
        )
        toc = self.toc_generator.get_toc()
        self.assertIn('introduction', toc['children'])
        self.assertEqual(toc['children']['introduction']
                         ['title'], "Introduction")
        self.assertEqual(toc['children']['introduction']
                         ['url'], "introduction")

    def test_nested_entries(self):
        """Test nested directory structure"""
        self.toc_generator.add_entry(
            Path("advanced/config.md"),
            "Configuration",
            "advanced/config"
        )
        toc = self.toc_generator.get_toc()
        self.assertIn('advanced', toc['children'])
        self.assertIn('config', toc['children']['advanced']['children'])
        self.assertEqual(
            toc['children']['advanced']['children']['config']['title'],
            "Configuration"
        )

    def test_multiple_levels(self):
        """Test multiple levels of nesting"""
        entries = [
            ("intro.md", "Introduction", "intro"),
            ("basics/start.md", "Getting Started", "basics/start"),
            ("basics/advanced/config.md", "Configuration", "basics/advanced/config"),
        ]
        for path, title, url in entries:
            self.toc_generator.add_entry(Path(path), title, url)

        toc = self.toc_generator.get_toc()

        # Check structure
        self.assertIn('intro', toc['children'])
        self.assertIn('basics', toc['children'])
        self.assertIn('start', toc['children']['basics']['children'])
        self.assertIn('advanced', toc['children']['basics']['children'])
        self.assertIn(
            'config',
            toc['children']['basics']['children']['advanced']['children']
        )

    def test_url_generation(self):
        """Test URL generation for different levels"""
        entries = [
            ("index.md", "Home", ""),
            ("docs/intro.md", "Introduction", "docs/intro"),
        ]
        for path, title, url in entries:
            self.toc_generator.add_entry(Path(path), title, url)

        toc = self.toc_generator.get_toc()
        self.assertEqual(toc['children']['index']['url'], "")
        self.assertEqual(
            toc['children']['docs']['children']['intro']['url'],
            "docs/intro"
        )


class DocumentationClaimsTests(TestCase):
    """Tests that verify the claims made in our documentation"""

    def setUp(self):
        self.test_dir = Path("test_files")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)

    def test_basic_frontmatter_example(self):
        """Test the basic frontmatter example from documentation"""
        content = """---
title: My Custom Page Title
tags: ['django', 'python', 'web']
is_public: false
custom_field: any value you want
---
Your content starts here"""

        test_file = self.test_dir / "basic_example.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        # Verify all documented fields
        self.assertEqual(context.title, "My Custom Page Title")
        self.assertEqual(context.tags, ['django', 'python', 'web'])
        self.assertFalse(context.is_public)
        self.assertEqual(
            context.custom_meta['custom_field'], 'any value you want')
        self.assertEqual(context.raw_content, "Your content starts here")

    def test_default_values(self):
        """Test the documented default values"""
        content = """# Just content"""
        test_file = self.test_dir / "defaults.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        # Verify documented defaults
        # Should default to filename
        self.assertEqual(context.title, "defaults")
        self.assertTrue(context.is_public)  # Default: True
        self.assertEqual(context.tags, [])  # Default: []
        self.assertEqual(context.custom_meta, {})  # Default: empty dict
        self.assertIsNone(context.next_page)  # Default: None
        self.assertIsNone(context.prev_page)  # Default: None

    def test_toc_structure(self):
        """Test the documented TOC structure example"""
        # Create test files matching documentation example
        files = {
            "introduction.md": "# Intro",
            "getting-started.md": "# Getting Started",
            "advanced/configuration.md": "# Configuration",
            "advanced/customization.md": "# Customization"
        }

        # Create files and build TOC
        toc_generator = TOCGenerator()
        for path, content in files.items():
            file_path = self.test_dir / path
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

            relative_path = Path(path)
            toc_generator.add_entry(
                relative_path,
                relative_path.stem.replace('-', ' ').title(),
                str(relative_path.with_suffix('')).replace('\\', '/')
            )

        toc = toc_generator.get_toc()

        # Verify the structure matches documentation example
        self.assertIn('introduction', toc['children'])
        self.assertIn('getting-started', toc['children'])
        self.assertIn('advanced', toc['children'])

        advanced = toc['children']['advanced']
        self.assertIn('configuration', advanced['children'])
        self.assertIn('customization', advanced['children'])

        # Verify URLs
        self.assertEqual(
            toc['children']['introduction']['url'],
            'introduction'
        )
        self.assertEqual(
            toc['children']['advanced']['children']['configuration']['url'],
            'advanced/configuration'
        )

    def test_nested_directory_urls(self):
        """Test URL generation for nested directories"""
        test_structure = {
            "docs/getting-started/installation.md": {
                "content": "# Installation",
                "expected_url": "docs/getting-started/installation"
            },
            "docs/advanced/config/database.md": {
                "content": "# Database Config",
                "expected_url": "docs/advanced/config/database"
            }
        }

        toc_generator = TOCGenerator()
        for path, info in test_structure.items():
            file_path = self.test_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(info["content"])

            relative_path = Path(path)
            toc_generator.add_entry(
                relative_path,
                relative_path.stem.title(),
                str(relative_path.with_suffix('')).replace('\\', '/')
            )

        toc = toc_generator.get_toc()

        # Verify deeply nested URLs
        self.assertEqual(
            toc['children']['docs']['children']['getting-started']
            ['children']['installation']['url'],
            'docs/getting-started/installation'
        )
        self.assertEqual(
            toc['children']['docs']['children']['advanced']
            ['children']['config']['children']['database']['url'],
            'docs/advanced/config/database'
        )

    def test_custom_meta_handling(self):
        """Test handling of custom metadata fields"""
        content = """---
title: Test Page
author: John Doe
version: 1.0
description: A test page
keywords: ['test', 'meta']
---
# Content"""

        test_file = self.test_dir / "custom_meta.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        # Verify custom meta fields
        self.assertEqual(context.custom_meta['author'], 'John Doe')
        self.assertEqual(context.custom_meta['version'], 1.0)
        self.assertEqual(context.custom_meta['description'], 'A test page')
        self.assertEqual(context.custom_meta['keywords'], ['test', 'meta'])


class CrazyWackyTests(TestCase):
    """Tests that try to break things in creative ways"""

    def setUp(self):
        self.test_dir = Path("test_files")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)

    def test_emoji_everywhere(self):
        """Test handling of emoji in filenames, titles, and content"""
        content = """---
title: 🚀 Rocket Page 🌟
tags: ['💻', '🐍', '🎨']
mood: 🤪
---
# 🎉 Welcome!
This is a 👻 ghost page with 🌈 rainbow content!"""

        test_file = self.test_dir / "🚀_page.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        self.assertEqual(context.title, "🚀 Rocket Page 🌟")
        self.assertEqual(context.tags, ['💻', '🐍', '🎨'])
        self.assertEqual(context.custom_meta['mood'], '🤪')

    def test_extremely_nested_directories(self):
        """Test ridiculously deep directory structures"""
        deep_path = "1/2/3/4/5/6/7/8/9/10/very/very/very/deep/file.md"

        file_path = self.test_dir / deep_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# Deep Content")

        toc_generator = TOCGenerator()
        toc_generator.add_entry(
            Path(deep_path),
            "Deep File",
            deep_path.replace('.md', '')
        )

        toc = toc_generator.get_toc()
        # Navigate to the deepest level
        current = toc['children']
        for part in deep_path.split('/')[:-1]:
            self.assertIn(part, current)
            current = current[part]['children']

    def test_mixed_case_chaos(self):
        """Test weird mixed case in filenames and paths"""
        paths = [
            "UpPeR/LoWeR/mIxEd.md",
            "SHOUTING/VERY_LOUD.md",
            "whisper/quiet.md",
            "ChAoS/eVeRyWhErE.md"
        ]

        toc_generator = TOCGenerator()
        for path in paths:
            file_path = self.test_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# Mixed Case Content")

            toc_generator.add_entry(
                Path(path),
                path.split('/')[-1].replace('.md', ''),
                path.replace('.md', '')
            )

        toc = toc_generator.get_toc()
        # Verify case sensitivity is maintained
        self.assertIn('UpPeR', toc['children'])
        self.assertIn('SHOUTING', toc['children'])

    def test_special_characters_mayhem(self):
        """Test handling of special characters in various places"""
        content = """---
title: "!@#$%^&*() Special"
tags: ['<script>', '"; DROP TABLE users;--']
html_injection: '<iframe src="evil.com"></iframe>'
---
# Special #{!} Characters
Some `code` with **bold** and *italic* and [link](http://example.com)"""

        test_file = self.test_dir / "special!@#.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        self.assertEqual(context.title, "!@#$%^&*() Special")
        self.assertEqual(context.tags, ['<script>', '"; DROP TABLE users;--'])

    def test_massive_frontmatter(self):
        """Test handling of extremely large frontmatter"""
        # Create huge frontmatter with lots of nested data
        huge_meta = {
            f"key_{i}": {
                f"nested_{j}": [f"value_{k}" for k in range(10)]
                for j in range(10)
            }
            for i in range(10)
        }

        content = "---\n"
        content += yaml.dump(huge_meta)
        content += "---\n# Content"

        test_file = self.test_dir / "huge_meta.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        self.assertEqual(
            context.custom_meta['key_0']['nested_0'][0],
            'value_0'
        )

    def test_empty_everything(self):
        """Test handling of empty or minimal content"""
        empty_cases = [
            "",  # Completely empty
            "---\n---",  # Empty frontmatter
            "---\n---\n",  # Empty frontmatter with newline
            "\n\n\n",  # Just newlines
            "---\ntitle:\ntags:\n---\n",  # Empty fields
        ]

        for i, content in enumerate(empty_cases):
            test_file = self.test_dir / f"empty_{i}.md"
            test_file.write_text(content)

            parser = FrontMatterParser(content, test_file)
            context = parser.get_context("test")

            # Should not raise exceptions and have default values
            self.assertTrue(hasattr(context, 'title'))
            self.assertTrue(hasattr(context, 'tags'))

    def test_unicode_madness(self):
        """Test handling of various Unicode characters"""
        content = """---
title: Über den Wölken ☁️
tags: ['🌈', '★', '☢️', '🎨']
quote: Let's "quote" some 'mixed' quotation marks
currency: €100 × ¥50 ÷ £30 = $???
math: ∑(τ × π) ≠ ∞
---
# ¯\_(ツ)_/¯
Testing `→` Unicode `←` handling!
"""
        # Write the file with explicit UTF-8 encoding
        test_file = self.test_dir / "unicode_☢️.md"
        test_file.write_text(content, encoding='utf-8')

        # Create parser with the content read from file to ensure proper encoding
        parser = FrontMatterParser(
            test_file.read_text(encoding='utf-8'), test_file)
        context = parser.get_context("test")

        self.assertEqual(context.title, 'Über den Wölken ☁️')
        self.assertEqual(context.custom_meta['math'], '∑(τ × π) ≠ ∞')

    def test_whitespace_chaos(self):
        """Test handling of various whitespace combinations"""
        content = """---
title:    Lots    Of    Spaces    
tags:     [   'tag1'   ,    'tag2'    ]     
spaces:   '    '
tabs:     '\t\t\t'
newlines: '\n\n\n'
---

    #    Weird    Spacing    

This     has     many     spaces     between     words"""

        test_file = self.test_dir / "spaces.md"
        test_file.write_text(content)

        parser = FrontMatterParser(content, test_file)
        context = parser.get_context("test")

        self.assertEqual(context.title.strip(), "Lots    Of    Spaces")
        self.assertEqual(context.tags, ['tag1', 'tag2'])
