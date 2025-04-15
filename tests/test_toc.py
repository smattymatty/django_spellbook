import unittest
from pathlib import Path

from django.test import override_settings

from django_spellbook.markdown.toc import TOCGenerator, TOCEntry


class TestTOCEntry(unittest.TestCase):
    def test_init_with_no_children(self):
        """Test TOCEntry initialization without children"""
        entry = TOCEntry(title="Test", url="/test")
        self.assertEqual(entry.title, "Test")
        self.assertEqual(entry.url, "/test")
        self.assertEqual(entry.children, {})

    def test_init_with_children(self):
        """Test TOCEntry initialization with children"""
        children = {"child": TOCEntry(title="Child", url="/child")}
        entry = TOCEntry(title="Parent", url="/parent", children=children)
        self.assertEqual(entry.title, "Parent")
        self.assertEqual(entry.url, "/parent")
        self.assertEqual(entry.children, children)


class TestTOCGenerator(unittest.TestCase):
    def setUp(self):
        self.toc = TOCGenerator()

    def test_root_initialization(self):
        """Test initial state of TOC generator"""
        self.assertEqual(self.toc.root.title, "root")
        self.assertEqual(self.toc.root.url, "")
        self.assertEqual(self.toc.root.children, {})

    def test_add_root_level_file(self):
        """Test adding a file at root level"""
        self.toc.add_entry(
            Path("index.md"),
            title="Home",
            url="base:home",
        )
        toc_dict = self.toc.get_toc()
        self.assertEqual(
            toc_dict["children"]["index"],
            {"title": "Home", "url": "base:home"}
        )

    def test_add_nested_file(self):
        """Test adding a file in nested directories"""
        self.toc.add_entry(
            Path("docs/guide/intro.md"),
            title="Introduction",
            url="/docs/guide/intro",
        )
        toc_dict = self.toc.get_toc()

        # Check the structure
        docs = toc_dict["children"]["docs"]
        self.assertEqual(docs["title"], "Docs")

        guide = docs["children"]["guide"]
        self.assertEqual(guide["title"], "Guide")

        intro = guide["children"]["intro"]
        self.assertEqual(intro["title"], "Introduction")
        self.assertEqual(intro["url"], "/docs/guide/intro")

    def test_dashes_replaced_with_spaces_in_titlles(self):
        """Test that dashes in titles are replaced with spaces"""
        self.toc.add_entry(
            Path("docs/guide/intro-to-django.md"),
            title="intro-to-django",
            url="/docs/guide/intro-to-django",
        )
        toc_dict = self.toc.get_toc()

        self.assertIn("Intro to Django",
                      toc_dict["children"]
                      ['docs']['children']['guide']['children']
                      ["intro-to-django"]['title']
                      )

    def test_auto_capitalization_of_title_in_words_longer_than_2_characters(self):
        """Test that titles are automatically capitalized if they are longer than 3 characters"""
        self.toc.add_entry(
            Path("docs/guide/when-to-use-django.md"),
            title="when-to-use-django",
            url="/docs/guide/When-to-use-Django",
        )
        toc_dict = self.toc.get_toc()

        self.assertIn("When to Use Django",
                      toc_dict["children"]
                      ['docs']['children']['guide']['children']
                      ["when-to-use-django"]['title']
                      )

    @override_settings(SPELLBOOK_MD_TITLEFY=False)
    def test_false_capitalization_of_title_in_words_longer_than_2_characters(self):
        """Test that titles are not automatically capitalized if SPELLBOOK_MD_TITLE_CAPITALIZATION is set to False"""
        self.toc.add_entry(
            Path("docs/guide/when-to-use-django.md"),
            title="when-to-use-django",
            url="/docs/guide/when-to-use-django",
        )
        toc_dict = self.toc.get_toc()

        self.assertIn("when-to-use-django",
                      toc_dict["children"]
                      ['docs']['children']['guide']['children']
                      ["when-to-use-django"]['title']
                      )

    def test_multiple_files_same_directory(self):
        """Test adding multiple files to the same directory"""
        self.toc.add_entry(
            Path("docs/first.md"),
            title="First",
            url="/docs/first",
        )
        self.toc.add_entry(
            Path("docs/second.md"),
            title="Second",
            url="/docs/second",
        )

        toc_dict = self.toc.get_toc()
        docs_children = toc_dict["children"]["docs"]["children"]

        self.assertEqual(docs_children["first"]["title"], "First")
        self.assertEqual(docs_children["second"]["title"], "Second")

    def test_directory_title_formatting(self):
        """Test directory name formatting in TOC"""
        self.toc.add_entry(
            Path("getting-started/quick-start.md"),
            title="Quick Start",
            url="/getting-started/quick-start",
        )

        toc_dict = self.toc.get_toc()
        dir_entry = toc_dict["children"]["getting-started"]
        self.assertEqual(dir_entry["title"], "Getting Started")

    def test_mixed_structure(self):
        """Test mixed structure with files at different levels"""
        entries = [
            ("index.md", "Home", "/"),
            ("about.md", "About", "/about"),
            ("docs/index.md", "Documentation", "/docs"),
            ("docs/guide/start.md", "Getting-started", "/docs/guide/start"),
            ("docs/guide/advanced.md", "Advanced", "/docs/guide/advanced"),
        ]

        for path, title, url in entries:
            self.toc.add_entry(Path(path), title, url)

        toc_dict = self.toc.get_toc()
        root_children = toc_dict["children"]

        # Check root level
        self.assertEqual(root_children["index"]["title"], "Home")
        self.assertEqual(root_children["about"]["title"], "About")

        # Check nested structure
        docs = root_children["docs"]
        self.assertEqual(docs["children"]["index"]["title"], "Documentation")

        guide = docs["children"]["guide"]
        self.assertEqual(guide["children"]["start"]
                         ["title"], "Getting Started")
        self.assertEqual(guide["children"]["advanced"]["title"], "Advanced")

    def test_sorting(self):
        """Test that entries are sorted alphabetically"""
        entries = [
            ("z.md", "Z", "/z"),
            ("a.md", "A", "/a"),
            ("m.md", "M", "/m"),
        ]

        for path, title, url in entries:
            self.toc.add_entry(Path(path), title, url)

        toc_dict = self.toc.get_toc()
        children_keys = list(toc_dict["children"].keys())
        self.assertEqual(children_keys, sorted(children_keys))

    def test_empty_toc(self):
        """Test getting TOC with no entries"""
        toc_dict = self.toc.get_toc()
        self.assertEqual(
            toc_dict,
            {"title": "root", "url": ""}
        )

    def test_complex_paths(self):
        """Test handling of complex paths"""
        self.toc.add_entry(
            Path("a/very/deep/nested/structure/file.md"),
            title="Deep File",
            url="/a/very/deep/nested/structure/file",
        )

        current = self.toc.get_toc()
        for part in ["a", "very", "deep", "nested", "structure"]:
            self.assertIn(part, current["children"])
            current = current["children"][part]

        self.assertEqual(
            current["children"]["file"]["title"],
            "Deep File"
        )


import os
import shutil
import tempfile
import datetime
from pathlib import Path

from django.test import TestCase

from django_spellbook.markdown.toc import TOCGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
from django_spellbook.markdown.context import SpellbookContext


class TOCIntegrationTest(TestCase):
    """Integration tests for TOC generation with URL pattern matching"""
    
    def setUp(self):
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create temp directories for spellbook and content
        self.spellbook_dir = os.path.join(self.temp_dir, 'django_spellbook')
        self.content_dir = os.path.join(self.temp_dir, 'content')
        os.makedirs(self.spellbook_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        
        # Set up the URL generator
        self.url_generator = URLViewGenerator('test_app', self.content_dir)
        self.url_generator.spellbook_dir = self.spellbook_dir
        
        # Create a mock context for processed files
        self.context = SpellbookContext(
            title='Test',
            created_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            updated_at=datetime.datetime(2024, 11, 10, 3, 29, 58, 8432),
            url_path='test',
            raw_content='# Test\nThis is a test',
        )
        
        # Initialize TOC generator
        self.toc_generator = TOCGenerator()
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def _create_processed_file(self, relative_url):
        """Helper to create a processed file with a specific relative URL"""
        return ProcessedFile(
            original_path=Path(f"/test/{relative_url}.md"),
            html_content="<h1>Test</h1>",
            template_path=Path(f"/test/templates/{relative_url}.html"),
            relative_url=relative_url,
            context=self.context
        )
    
    def test_toc_matches_generated_urls(self):
        """Test that TOC URLs match the URL patterns generated by URLViewGenerator"""
        # Process files with different path structures including problematic dash patterns
        processed_files = [
            self._create_processed_file("index"),
            self._create_processed_file("----first_blog"),
            self._create_processed_file("lifestyle/--digital-minimalism"),
            self._create_processed_file("blocks/practice"),
            self._create_processed_file("blocks/-quote"),
            self._create_processed_file("tech/sustainable-tech")
        ]
        
        # Generate URLs
        self.url_generator.generate_urls_and_views(processed_files, {})
        
        # Read the generated urls.py file
        urls_file_path = os.path.join(self.spellbook_dir, 'urls_test_app.py')
        self.assertTrue(os.path.exists(urls_file_path), "URLs file was not created")
        
        with open(urls_file_path, 'r') as f:
            urls_content = f.read()
        
        # Add TOC entries for the same files
        for file in processed_files:
            path_parts = file.relative_url.split('/')
            file_name = path_parts[-1]
            dir_parts = path_parts[:-1]
            
            # Construct file path with .md extension
            if dir_parts:
                file_path = Path(os.path.join(*dir_parts, f"{file_name}.md"))
            else:
                file_path = Path(f"{file_name}.md")
            
            # Add entry to TOC with URL matching the processed file's URL pattern
            view_name = file.relative_url.replace('/', '_')
            self.toc_generator.add_entry(
                file_path=file_path,
                title=file_name.replace('-', ' ').title(),
                url=view_name
            )
        
        toc = self.toc_generator.get_toc()
        
        # Verify URL patterns in generated urls.py match expected formats
        self.assertIn("path('index/', index, name='index')", urls_content)
        self.assertIn("path('first_blog/', first_blog, name='first_blog')", urls_content)
        self.assertIn("path('lifestyle/digital-minimalism/', lifestyle_digital_minimalism, name='lifestyle_digital-minimalism')", urls_content)
        
        # Verify TOC URLs match function names used in views/urls
        self.assertEqual(toc['children']['index']['url'], 'index')
        self.assertEqual(toc['children']['----first_blog']['url'], 'first_blog')
        
        # Verify TOC structure for nested paths
        lifestyle = toc['children']['lifestyle']
        self.assertEqual(lifestyle['children']['--digital-minimalism']['url'], 'lifestyle_digital-minimalism')
        
        blocks = toc['children']['blocks']
        self.assertEqual(blocks['children']['practice']['url'], 'blocks_practice')
        self.assertEqual(blocks['children']['-quote']['url'], 'blocks_quote')
    
    def test_complex_nested_toc_structure(self):
        """Test TOC generation with complex nested structure with various dash patterns"""
        # Create complex nested structure with files at different levels
        processed_files = [
            self._create_processed_file("docs/installation"),
            self._create_processed_file("docs/--api-reference"),
            self._create_processed_file("docs/api/--endpoints"),
            self._create_processed_file("blog/2023/--year-review"),
            self._create_processed_file("blog/lifestyle/--digital-minimalism/part-1"),
            self._create_processed_file("blog/lifestyle/--digital-minimalism/part-2"),
        ]
        
        # Generate URLs
        self.url_generator.generate_urls_and_views(processed_files, {})
        
        # Add TOC entries for each file
        for file in processed_files:
            path_parts = file.relative_url.split('/')
            file_name = path_parts[-1]
            dir_parts = path_parts[:-1]
            
            if dir_parts:
                file_path = Path(os.path.join(*dir_parts, f"{file_name}.md"))
            else:
                file_path = Path(f"{file_name}.md")
            
            view_name = file.relative_url.replace('/', '_')
            self.toc_generator.add_entry(
                file_path=file_path,
                title=file_name.replace('-', ' ').title(),
                url=view_name
            )
        
        toc = self.toc_generator.get_toc()
        
        # Verify TOC structure matches expected structure
        docs = toc['children']['docs']
        self.assertEqual(docs['children']['installation']['url'], 'docs_installation')
        self.assertEqual(docs['children']['--api-reference']['url'], 'docs_api-reference')
        
        api = docs['children']['api']
        self.assertEqual(api['children']['--endpoints']['url'], 'docs_api_endpoints')
        
        blog = toc['children']['blog']
        blog_2023 = blog['children']['2023']
        self.assertEqual(blog_2023['children']['--year-review']['url'], 'blog_2023_year-review')
        
        # Check deeply nested structure with multiple levels
        lifestyle = blog['children']['lifestyle']
        digital_min = lifestyle['children']['--digital-minimalism']
        self.assertEqual(digital_min['children']['part-1']['url'], 
                         'blog_lifestyle_digital-minimalism_part-1')
        self.assertEqual(digital_min['children']['part-2']['url'], 
                         'blog_lifestyle_digital-minimalism_part-2')
        
        # Read generated urls.py to verify actual URL patterns
        urls_file_path = os.path.join(self.spellbook_dir, 'urls_test_app.py')
        with open(urls_file_path, 'r') as f:
            urls_content = f.read()
        
        # Verify URL patterns match TOC structure
        self.assertIn("path('docs/installation/', docs_installation, name='docs_installation')", urls_content)
        self.assertIn("path('docs/api-reference/', docs_api_reference, name='docs_api-reference')", urls_content)
        self.assertIn("path('blog/lifestyle/digital-minimalism/part-1/', blog_lifestyle_digital_minimalism_part_1, name='blog_lifestyle_digital-minimalism_part-1')", urls_content)