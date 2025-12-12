# tests/test_directory_index.py

import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

from django.test import TestCase

from django_spellbook.management.commands.processing.directory_index import DirectoryIndexBuilder
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext


class TestDirectoryIndexBuilder(TestCase):
    """Test DirectoryIndexBuilder functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = DirectoryIndexBuilder('test_app', 'docs')

    def _create_processed_file(
        self,
        path: str,
        title: str = "Test Page",
        relative_url: str = None,
        published: datetime = None,
        tags: list = None
    ) -> ProcessedFile:
        """Helper to create a ProcessedFile."""
        file_path = Path(path)
        if relative_url is None:
            # Extract relative path from full path (remove leading slash and content root)
            # e.g., "/content/docs/guide.md" -> "content/docs/guide"
            parts = [p for p in file_path.parts if p not in ('/', '')]
            if len(parts) > 0:
                # Remove .md extension
                parts[-1] = file_path.stem
                relative_url = '/'.join(parts)
            else:
                relative_url = file_path.stem

        context = SpellbookContext(
            title=title,
            url_path=relative_url,
            raw_content="Test content",
            is_public=True,
            published=published,
            tags=tags or []
        )

        return ProcessedFile(
            original_path=file_path,
            html_content="<p>Test</p>",
            template_path=Path(f"/templates/{relative_url}.html"),
            relative_url=relative_url,
            context=context
        )

    def test_groups_files_by_directory(self):
        """Files are correctly grouped by parent directory."""
        pf1 = self._create_processed_file("/content/docs/guide.md")
        pf2 = self._create_processed_file("/content/docs/tutorial.md")
        pf3 = self._create_processed_file("/content/api/reference.md")

        groups = self.builder._group_by_directory([pf1, pf2, pf3])

        self.assertEqual(len(groups), 2)
        self.assertIn(Path("content/docs"), groups)
        self.assertIn(Path("content/api"), groups)
        self.assertEqual(len(groups[Path("content/docs")]), 2)
        self.assertEqual(len(groups[Path("content/api")]), 1)

    def test_detects_subdirectories(self):
        """Subdirectories are detected and counted correctly."""
        pf1 = self._create_processed_file("/content/docs/getting-started/intro.md")
        pf2 = self._create_processed_file("/content/docs/getting-started/install.md")
        pf3 = self._create_processed_file("/content/docs/advanced/config.md")
        pf4 = self._create_processed_file("/content/docs/guide.md")

        subdirs = self.builder._detect_subdirectories(
            Path("content/docs"),
            [pf1, pf2, pf3, pf4]
        )

        self.assertEqual(len(subdirs), 2)
        subdir_titles = [s['title'] for s in subdirs]
        self.assertIn('Getting Started', subdir_titles)
        self.assertIn('Advanced', subdir_titles)

        # Check page counts
        for subdir in subdirs:
            if subdir['title'] == 'Getting Started':
                self.assertEqual(subdir['page_count'], 2)
            elif subdir['title'] == 'Advanced':
                self.assertEqual(subdir['page_count'], 1)

    def test_generates_view_function(self):
        """View function code is valid Python."""
        context_data = {
            'directory_name': 'Docs',
            'directory_path': '/docs/',
            'subdirectories': [],
            'pages': [{'title': 'Guide', 'url': '/docs/guide/', 'published': None, 'modified': None, 'tags': [], 'description': None}]
        }

        view_func = self.builder._generate_view_function(Path("docs"), context_data)

        self.assertIn('def directory_index_docs(request):', view_func)
        self.assertIn("render(request, 'django_spellbook/directory_index/default.html', context)", view_func)
        self.assertIn("'directory_name': 'Docs'", view_func)

    def test_generates_url_pattern(self):
        """URL pattern code is valid Django pattern."""
        url_pattern = self.builder._generate_url_pattern(Path("docs"))

        # With url_prefix='docs' and directory='docs', the prefix is removed from path
        # since it will be added by include() in main urls.py
        # Result: path('', ...) which becomes 'docs/' when included at 'docs/'
        self.assertIn("path('', views.directory_index_docs", url_pattern)
        self.assertIn("name='test_app_directory_index_docs'", url_pattern)

    def test_skips_directories_with_index_conflict(self):
        """Directories with index.md are skipped."""
        # File that claims the directory root URL
        # The builder has url_prefix='docs', so directory 'content/docs' would be at '/docs/content/docs/'
        # A file with relative_url 'content/docs' would generate '/docs/content/docs/'
        pf1 = self._create_processed_file("content/docs/index.md", relative_url="content/docs")
        pf2 = self._create_processed_file("content/docs/guide.md", relative_url="content/docs/guide")

        has_conflict = self.builder._has_index_conflict(
            Path("content/docs"),
            [pf1, pf2]
        )

        self.assertTrue(has_conflict)

    def test_no_conflict_when_safe(self):
        """No conflict when directory is safe to generate index."""
        pf1 = self._create_processed_file("/content/docs/guide.md")
        pf2 = self._create_processed_file("/content/docs/tutorial.md")

        has_conflict = self.builder._has_index_conflict(
            Path("content/docs"),
            [pf1, pf2]
        )

        self.assertFalse(has_conflict)

    def test_alphabetical_sorting(self):
        """Subdirectories and pages are sorted alphabetically."""
        pf1 = self._create_processed_file("/content/docs/zebra.md", title="Zebra")
        pf2 = self._create_processed_file("/content/docs/apple.md", title="Apple")
        pf3 = self._create_processed_file("/content/docs/middle.md", title="Middle")

        pages = self.builder._collect_page_metadata([pf1, pf2, pf3])

        self.assertEqual(pages[0]['title'], 'Apple')
        self.assertEqual(pages[1]['title'], 'Middle')
        self.assertEqual(pages[2]['title'], 'Zebra')

    def test_metadata_extraction(self):
        """Page metadata is extracted correctly."""
        published_date = datetime(2025, 12, 8)
        pf = self._create_processed_file(
            "/content/docs/guide.md",
            title="User Guide",
            published=published_date,
            tags=['intro', 'basics']
        )

        pages = self.builder._collect_page_metadata([pf])

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]['title'], 'User Guide')
        self.assertEqual(pages[0]['published'], published_date)  # Now returns datetime object, not string
        self.assertEqual(pages[0]['tags'], ['intro', 'basics'])

    def test_handles_missing_metadata(self):
        """Missing metadata fields don't break generation."""
        pf = self._create_processed_file(
            "/content/docs/guide.md",
            title="Guide",
            published=None,
            tags=None
        )

        pages = self.builder._collect_page_metadata([pf])

        self.assertEqual(len(pages), 1)
        self.assertIsNone(pages[0]['published'])
        self.assertIsNone(pages[0]['modified'])
        self.assertEqual(pages[0]['tags'], [])

    def test_title_fallback(self):
        """Falls back to filename when title missing."""
        context = SpellbookContext(
            title=None,  # No title
            url_path="my-guide",
            raw_content="Test",
            is_public=True
        )

        pf = ProcessedFile(
            original_path=Path("/content/docs/my-guide.md"),
            html_content="<p>Test</p>",
            template_path=Path("/templates/my-guide.html"),
            relative_url="my-guide",
            context=context
        )

        pages = self.builder._collect_page_metadata([pf])

        self.assertEqual(pages[0]['title'], 'My Guide')  # Fallback to filename (with spaces)

    def test_url_prefix_handling(self):
        """URL prefix is NOT included (added by include() in main urls)."""
        builder = DirectoryIndexBuilder('test_app', 'docs')
        pf = self._create_processed_file("/content/guide.md", relative_url="guide")

        page_url = builder._build_page_url(pf.relative_url)

        # No prefix, no leading slash (will be added by include())
        self.assertEqual(page_url, 'guide/')

    def test_nested_directories(self):
        """Multi-level nesting works correctly."""
        pf1 = self._create_processed_file("/content/docs/api/v1/endpoints.md")
        pf2 = self._create_processed_file("/content/docs/api/v2/endpoints.md")
        pf3 = self._create_processed_file("/content/docs/api/auth.md")

        groups = self.builder._group_by_directory([pf1, pf2, pf3])

        self.assertIn(Path("content/docs/api/v1"), groups)
        self.assertIn(Path("content/docs/api/v2"), groups)
        self.assertIn(Path("content/docs/api"), groups)

    def test_build_indexes_returns_views_and_urls(self):
        """build_indexes returns both view functions and URL patterns."""
        pf1 = self._create_processed_file("/content/docs/guide.md")
        pf2 = self._create_processed_file("/content/docs/tutorial.md")

        views, urls = self.builder.build_indexes([pf1, pf2])

        self.assertGreater(len(views), 0)
        self.assertGreater(len(urls), 0)
        self.assertEqual(len(views), len(urls))

    def test_empty_file_list(self):
        """Empty file list returns empty results."""
        views, urls = self.builder.build_indexes([])

        self.assertEqual(len(views), 0)
        self.assertEqual(len(urls), 0)

    def test_humanize_directory_name(self):
        """Directory names are humanized correctly."""
        self.assertEqual(
            self.builder._humanize_directory_name(Path("getting-started")),
            "Getting Started"
        )
        self.assertEqual(
            self.builder._humanize_directory_name(Path("api-reference")),
            "API Reference"
        )
        self.assertEqual(
            self.builder._humanize_directory_name(Path("faq")),
            "FAQ"
        )

    def test_build_directory_url(self):
        """Directory URLs are built correctly with prefix."""
        builder = DirectoryIndexBuilder('test_app', 'docs')

        url = builder._build_directory_url(Path("guides"))

        # No leading slash, no prefix (added by include())
        self.assertEqual(url, 'guides/')

    def test_build_directory_url_no_prefix(self):
        """Directory URLs work without prefix."""
        builder = DirectoryIndexBuilder('test_app', '')

        url = builder._build_directory_url(Path("guides"))

        # No leading slash, no prefix
        self.assertEqual(url, 'guides/')

    def test_root_directory_url(self):
        """Root directory URL is handled correctly."""
        builder = DirectoryIndexBuilder('test_app', 'docs')

        url = builder._build_directory_url(Path("."))

        # Empty string for root (will be at include prefix)
        self.assertEqual(url, '')

    def test_context_includes_directory_index_flag(self):
        """Context includes is_directory_index flag."""
        pf1 = self._create_processed_file("/content/docs/guide.md")
        pf2 = self._create_processed_file("/content/docs/tutorial.md")

        context = self.builder._collect_directory_context(
            Path("content/docs"),
            [pf1, pf2],
            [pf1, pf2]
        )

        self.assertTrue(context['is_directory_index'])

    def test_view_function_includes_toc_reference(self):
        """Generated view functions include TOC in context."""
        context_data = {
            'directory_name': 'Docs',
            'directory_path': '/docs/',
            'subdirectories': [],
            'pages': []
        }

        view_func = self.builder._generate_view_function(Path("docs"), context_data)

        self.assertIn("context['toc'] = TOC", view_func)
