# tests/test_navigation.py

import unittest
from unittest.mock import Mock
from pathlib import Path
from django.test import TestCase

from django_spellbook.management.commands.processing.navigation import NavigationBuilder
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext


class TestNavigationBuilder(TestCase):
    """Tests for the NavigationBuilder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("/test/docs")

    def _create_processed_file(self, filename: str, app: str = "blog", directory: Path = None, prev=None, next=None):
        """Helper to create a ProcessedFile with SpellbookContext."""
        if directory is None:
            directory = self.test_dir

        # relative_url should match what get_clean_url produces (removes leading dashes, keeps internal dashes)
        relative_url = filename.replace('.md', '')

        # Create a SpellbookContext with required fields
        context = SpellbookContext(
            title=filename.replace('.md', '').replace('-', ' ').title(),
            url_path=f"test/{relative_url}",
            raw_content=f"# {filename}\n\nTest content",
            prev_page=prev,
            next_page=next
        )

        # Add namespace for navigation grouping
        context.namespace = app

        return ProcessedFile(
            original_path=directory / filename,
            html_content=f"<h1>{filename}</h1>",
            template_path=Path(f"/templates/{filename}.html"),
            relative_url=relative_url,  # This is what gets passed to get_clean_url
            context=context
        )

    def test_empty_file_list(self):
        """Test that empty file list doesn't raise errors."""
        NavigationBuilder.build_navigation([], "blog")
        # Should complete without error

    def test_single_file_no_navigation(self):
        """Test that a single file has no prev/next links."""
        file = self._create_processed_file("intro.md")

        NavigationBuilder.build_navigation([file], "blog")

        self.assertIsNone(file.context.prev_page)
        self.assertIsNone(file.context.next_page)

    def test_two_files_alphabetical_navigation(self):
        """Test navigation between two files sorted alphabetically."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md")

        NavigationBuilder.build_navigation([file2, file1], "blog")  # Unsorted order

        # file1 should have next to file2
        self.assertIsNone(file1.context.prev_page)
        self.assertEqual(file1.context.next_page, "blog:02-setup")  # Dashes preserved in URL

        # file2 should have prev to file1
        self.assertEqual(file2.context.prev_page, "blog:01-intro")  # Dashes preserved in URL
        self.assertIsNone(file2.context.next_page)

    def test_three_files_complete_chain(self):
        """Test navigation chain with three files."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md")
        file3 = self._create_processed_file("03-usage.md")

        NavigationBuilder.build_navigation([file3, file1, file2], "blog")

        # file1: no prev, next to file2
        self.assertIsNone(file1.context.prev_page)
        self.assertEqual(file1.context.next_page, "blog:02-setup")

        # file2: prev to file1, next to file3
        self.assertEqual(file2.context.prev_page, "blog:01-intro")
        self.assertEqual(file2.context.next_page, "blog:03-usage")

        # file3: prev to file2, no next
        self.assertEqual(file3.context.prev_page, "blog:02-setup")
        self.assertIsNone(file3.context.next_page)

    def test_alphabetical_sorting(self):
        """Test that files are sorted alphabetically."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md")
        file3 = self._create_processed_file("03-usage.md")

        # Pass files in random order
        NavigationBuilder.build_navigation([file2, file3, file1], "blog")

        # Should be sorted alphabetically
        self.assertIsNone(file1.context.prev_page)
        self.assertEqual(file1.context.next_page, "blog:02-setup")

        self.assertEqual(file2.context.prev_page, "blog:01-intro")
        self.assertEqual(file2.context.next_page, "blog:03-usage")

        self.assertEqual(file3.context.prev_page, "blog:02-setup")
        self.assertIsNone(file3.context.next_page)

    def test_directory_boundaries_respected(self):
        """Test that files in different directories don't link to each other."""
        # Files in root directory
        file1 = self._create_processed_file("intro.md", directory=self.test_dir)

        # Files in subdirectory
        subdir = self.test_dir / "advanced"
        file2 = self._create_processed_file("performance.md", directory=subdir)

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Both files should have no navigation (different directories)
        self.assertIsNone(file1.context.prev_page)
        self.assertIsNone(file1.context.next_page)
        self.assertIsNone(file2.context.prev_page)
        self.assertIsNone(file2.context.next_page)

    def test_app_namespace_used_in_urls(self):
        """Test that the provided app parameter is used in generated URLs."""
        file1 = self._create_processed_file("aaa.md")  # First alphabetically
        file2 = self._create_processed_file("zzz.md")  # Last alphabetically

        # Pass "myapp" as the content_app
        NavigationBuilder.build_navigation([file1, file2], "myapp")

        # Both files should use "myapp:" namespace
        self.assertEqual(file1.context.next_page, "myapp:zzz")
        self.assertEqual(file2.context.prev_page, "myapp:aaa")

    def test_frontmatter_override_prev(self):
        """Test that frontmatter prev override is respected."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md", prev="blog:custom_prev")
        file3 = self._create_processed_file("03-usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # file2 should use frontmatter override for prev
        self.assertEqual(file2.context.prev_page, "blog:custom_prev")
        # But next should still be auto-calculated
        self.assertEqual(file2.context.next_page, "blog:03-usage")

    def test_frontmatter_override_next(self):
        """Test that frontmatter next override is respected."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md", next="blog:custom_next")
        file3 = self._create_processed_file("03-usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # file2 should use frontmatter override for next
        self.assertEqual(file2.context.next_page, "blog:custom_next")
        # But prev should still be auto-calculated
        self.assertEqual(file2.context.prev_page, "blog:01-intro")

    def test_frontmatter_override_both(self):
        """Test that both prev and next frontmatter overrides work together."""
        file1 = self._create_processed_file("01-intro.md")
        file2 = self._create_processed_file("02-setup.md", prev="blog:custom_prev", next="blog:custom_next")
        file3 = self._create_processed_file("03-usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # file2 should use both frontmatter overrides
        self.assertEqual(file2.context.prev_page, "blog:custom_prev")
        self.assertEqual(file2.context.next_page, "blog:custom_next")

    def test_namespaced_url_generation(self):
        """Test that namespaced URLs are generated correctly."""
        file1 = self._create_processed_file("intro.md")
        file2 = self._create_processed_file("setup.md")

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Check URL format: app:url_name
        self.assertIn(":", file1.context.next_page)
        self.assertEqual(file1.context.next_page, "blog:setup")

    def test_different_directory_same_app(self):
        """Test that files in different directories of the same app don't link."""
        dir1 = Path("/test/docs/basics")
        dir2 = Path("/test/docs/advanced")

        file1 = self._create_processed_file("intro.md", app="docs", directory=dir1)
        file2 = self._create_processed_file("performance.md", app="docs", directory=dir2)

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Same app but different directories - should not link
        self.assertIsNone(file1.context.next_page)
        self.assertIsNone(file2.context.prev_page)

    def test_multiple_files_same_directory(self):
        """Test navigation with many files in the same directory."""
        files = [
            self._create_processed_file(f"{i:02d}-file.md")
            for i in range(1, 6)
        ]

        NavigationBuilder.build_navigation(files, "blog")

        # First file
        self.assertIsNone(files[0].context.prev_page)
        self.assertEqual(files[0].context.next_page, "blog:02-file")

        # Middle files
        for i in range(1, 4):
            self.assertEqual(files[i].context.prev_page, f"blog:{i:02d}-file")
            self.assertEqual(files[i].context.next_page, f"blog:{i+2:02d}-file")

        # Last file
        self.assertEqual(files[4].context.prev_page, "blog:04-file")
        self.assertIsNone(files[4].context.next_page)

    def test_case_insensitive_sorting(self):
        """Test that file sorting is case-insensitive."""
        file_upper = self._create_processed_file("AAA.md")
        file_lower = self._create_processed_file("bbb.md")

        NavigationBuilder.build_navigation([file_lower, file_upper], "blog")

        # AAA should come before bbb (case-insensitive)
        self.assertEqual(file_upper.context.next_page, "blog:bbb")
        self.assertEqual(file_lower.context.prev_page, "blog:AAA")


class TestNavigationBuilderEdgeCases(TestCase):
    """Test edge cases and error handling for NavigationBuilder."""

    def _create_minimal_file(self, filename: str, app: str = "test"):
        """Helper to create a minimal ProcessedFile."""
        context = SpellbookContext(
            title="Test",
            url_path="test/path",
            raw_content="content"
        )
        context.namespace = app

        return ProcessedFile(
            original_path=Path(f"/test/{filename}"),
            html_content="<p>test</p>",
            template_path=Path("/templates/test.html"),
            relative_url=filename.replace('.md', ''),
            context=context
        )

    def test_none_namespace_handling(self):
        """Test handling of files without namespace."""
        file1 = self._create_minimal_file("file1.md", app="default")
        file2 = self._create_minimal_file("file2.md", app="default")

        # Should not raise error
        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Navigation should still work
        self.assertIsNotNone(file1.context.next_page)

    def test_special_characters_in_filename(self):
        """Test handling of special characters in filenames."""
        file1 = self._create_minimal_file("file-with-dashes.md")
        file2 = self._create_minimal_file("file_with_underscores.md")

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Should generate valid namespaced URLs with the provided app
        self.assertIn(":", file1.context.next_page)
        self.assertIn("blog:", file1.context.next_page)


class TestPathBasedNavigation(TestCase):
    """Tests for path-based navigation frontmatter overrides."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("/test/docs")

    def _create_processed_file(self, filename: str, app: str = "blog", directory: Path = None, prev=None, next=None):
        """Helper to create a ProcessedFile with SpellbookContext."""
        if directory is None:
            directory = self.test_dir

        # relative_url should match what get_clean_url produces
        relative_url = filename.replace('.md', '')

        context = SpellbookContext(
            title=filename.replace('.md', '').replace('-', ' ').title(),
            url_path=f"test/{relative_url}",
            raw_content=f"# {filename}\n\nTest content",
            prev_page=prev,
            next_page=next
        )
        context.namespace = app

        return ProcessedFile(
            original_path=directory / filename,
            html_content=f"<h1>{filename}</h1>",
            template_path=Path(f"/templates/{filename}.html"),
            relative_url=relative_url,
            context=context
        )

    def test_is_namespaced_format_with_colon(self):
        """Test detection of namespaced format."""
        self.assertTrue(NavigationBuilder._is_namespaced_format("blog:page"))
        self.assertTrue(NavigationBuilder._is_namespaced_format("docs:---introduction"))
        self.assertTrue(NavigationBuilder._is_namespaced_format("my_app:sub_page"))

    def test_is_namespaced_format_no_colon(self):
        """Test detection of path format (no colon)."""
        self.assertFalse(NavigationBuilder._is_namespaced_format("introduction"))
        self.assertFalse(NavigationBuilder._is_namespaced_format("guides/setup"))
        self.assertFalse(NavigationBuilder._is_namespaced_format("path/to/page"))

    def test_is_namespaced_format_edge_cases(self):
        """Test edge cases for format detection."""
        # Colon after slash = path format
        self.assertFalse(NavigationBuilder._is_namespaced_format("path/to:file"))
        # Empty before colon = path format
        self.assertFalse(NavigationBuilder._is_namespaced_format(":something"))
        # Slash before colon = path format
        self.assertFalse(NavigationBuilder._is_namespaced_format("path/:page"))

    def test_path_based_override_simple(self):
        """Test path-based frontmatter override with simple filename."""
        file1 = self._create_processed_file("intro.md")
        file2 = self._create_processed_file("setup.md", prev="intro")  # Path-based
        file3 = self._create_processed_file("usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # file2 should resolve "intro" to "blog:intro"
        self.assertEqual(file2.context.prev_page, "blog:intro")
        # Auto next should still work
        self.assertEqual(file2.context.next_page, "blog:usage")

    def test_path_based_override_with_slash(self):
        """Test path-based frontmatter override with directory path."""
        # Create files in different directories
        dir1 = Path("/test/docs/basics")
        dir2 = Path("/test/docs/advanced")

        file1 = self._create_processed_file("intro.md", directory=dir1)
        file2 = self._create_processed_file("config.md", directory=dir2, prev="basics/intro")  # Path with slash

        # Build navigation for both files
        NavigationBuilder.build_navigation([file1, file2], "blog")

        # file2 should resolve "basics/intro" - but won't find it (different directory)
        # So it falls back to constructing the URL
        self.assertEqual(file2.context.prev_page, "blog:basics_intro")

    def test_namespaced_override_still_works(self):
        """Test that namespaced format overrides still work."""
        file1 = self._create_processed_file("intro.md")
        file2 = self._create_processed_file("setup.md", prev="blog:custom-page")  # Namespaced
        file3 = self._create_processed_file("usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # file2 should use namespaced override as-is
        self.assertEqual(file2.context.prev_page, "blog:custom-page")

    def test_mixed_path_and_namespaced(self):
        """Test mixing path-based and namespaced overrides."""
        file1 = self._create_processed_file("intro.md")
        file2 = self._create_processed_file("setup.md", prev="intro", next="docs:conclusion")  # Mixed!
        file3 = self._create_processed_file("usage.md")

        NavigationBuilder.build_navigation([file1, file2, file3], "blog")

        # prev should resolve path "intro" to "blog:intro"
        self.assertEqual(file2.context.prev_page, "blog:intro")
        # next should use namespaced as-is
        self.assertEqual(file2.context.next_page, "docs:conclusion")

    def test_path_with_dashes(self):
        """Test path-based override with dashes in filename."""
        file1 = self._create_processed_file("01-introduction.md")
        file2 = self._create_processed_file("02-setup.md", prev="01-introduction")  # Path with dashes

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Should resolve to namespaced format
        self.assertEqual(file2.context.prev_page, "blog:01-introduction")

    def test_namespaced_with_triple_dash(self):
        """Test namespaced format with triple dash in URL name."""
        file1 = self._create_processed_file("---intro.md")
        file2 = self._create_processed_file("setup.md", prev="blog:---intro")  # Namespaced with dashes

        NavigationBuilder.build_navigation([file1, file2], "blog")

        # Should recognize as namespaced and use as-is
        self.assertEqual(file2.context.prev_page, "blog:---intro")
