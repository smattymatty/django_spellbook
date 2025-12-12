# tests/test_directory_metadata.py

from django.test import TestCase
from django.template import Template, Context
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from unittest.mock import Mock

from django_spellbook.management.commands.processing.directory_index import DirectoryIndexBuilder
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext


class TestDirectoryStatsCalculation(TestCase):
    """Test the _calculate_directory_stats() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = DirectoryIndexBuilder('test_app', 'docs')

    def _create_processed_file(self, relative_url, modified=None, published=None):
        """Helper to create a ProcessedFile with minimal context."""
        context = Mock(spec=SpellbookContext)
        context.modified = modified
        context.published = published
        context.title = f"Page {relative_url}"

        return ProcessedFile(
            original_path=Path(f"content/{relative_url}.md"),
            html_content="<p>Test</p>",
            template_path=Path("templates/base.html"),
            relative_url=relative_url,
            context=context
        )

    def test_direct_pages_count(self):
        """Direct pages count matches files in current directory."""
        # Create files directly in 'docs'
        files = [
            self._create_processed_file('intro'),
            self._create_processed_file('setup'),
            self._create_processed_file('guide'),
        ]

        all_files = files + [
            self._create_processed_file('advanced/topics'),  # In subdirectory
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, all_files
        )

        self.assertEqual(stats['direct_pages'], 3)

    def test_recursive_count_includes_subdirectories(self):
        """Total pages count includes subdirectories recursively."""
        files = [
            self._create_processed_file('intro'),
            self._create_processed_file('setup'),
        ]

        all_files = files + [
            self._create_processed_file('advanced/topics'),
            self._create_processed_file('advanced/deep/nested'),
            self._create_processed_file('guides/beginner'),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, all_files
        )

        # Root directory contains all 5 files
        self.assertEqual(stats['total_pages'], 5)

    def test_recursive_count_for_subdirectory(self):
        """Total pages count works for subdirectories."""
        files = [
            self._create_processed_file('advanced/topics'),
        ]

        all_files = [
            self._create_processed_file('intro'),  # Not in advanced/
            self._create_processed_file('advanced/topics'),
            self._create_processed_file('advanced/deep/nested'),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('advanced'), files, all_files
        )

        # advanced/ directory contains 2 files (topics and deep/nested)
        self.assertEqual(stats['total_pages'], 2)
        self.assertEqual(stats['direct_pages'], 1)

    def test_last_updated_from_modified_date(self):
        """Last updated uses modified date when available."""
        date1 = datetime(2025, 1, 1)
        date2 = datetime(2025, 12, 10)  # Most recent
        date3 = datetime(2025, 6, 15)

        files = [
            self._create_processed_file('intro', modified=date1),
            self._create_processed_file('setup', modified=date2),
            self._create_processed_file('guide', modified=date3),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, files
        )

        self.assertEqual(stats['last_updated'], date2)

    def test_last_updated_falls_back_to_published(self):
        """Last updated uses published date if modified is None."""
        published1 = datetime(2025, 1, 1)
        published2 = datetime(2025, 12, 10)  # Most recent

        files = [
            self._create_processed_file('intro', modified=None, published=published1),
            self._create_processed_file('setup', modified=None, published=published2),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, files
        )

        self.assertEqual(stats['last_updated'], published2)

    def test_last_updated_mixed_modified_and_published(self):
        """Last updated handles mix of modified and published dates."""
        modified_date = datetime(2025, 11, 1)
        published_date = datetime(2025, 12, 10)  # Most recent (but published only)

        files = [
            self._create_processed_file('intro', modified=modified_date, published=datetime(2025, 1, 1)),
            self._create_processed_file('setup', modified=None, published=published_date),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, files
        )

        self.assertEqual(stats['last_updated'], published_date)

    def test_last_updated_none_when_no_dates(self):
        """Last updated is None when no files have dates."""
        files = [
            self._create_processed_file('intro', modified=None, published=None),
            self._create_processed_file('setup', modified=None, published=None),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, files
        )

        self.assertIsNone(stats['last_updated'])

    def test_subdirectory_count(self):
        """Subdirectory count matches immediate child directories."""
        files = [
            self._create_processed_file('intro'),
        ]

        all_files = files + [
            self._create_processed_file('guides/beginner'),
            self._create_processed_file('guides/advanced'),
            self._create_processed_file('advanced/topics'),
            self._create_processed_file('reference/api'),
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, all_files
        )

        # Root has 3 immediate subdirectories: guides, advanced, reference
        self.assertEqual(stats['subdirectory_count'], 3)

    def test_empty_directory_stats(self):
        """Empty directory returns zeros/None."""
        stats = self.builder._calculate_directory_stats(
            Path('.'), [], []
        )

        self.assertEqual(stats['total_pages'], 0)
        self.assertEqual(stats['direct_pages'], 0)
        self.assertEqual(stats['subdirectory_count'], 0)
        self.assertIsNone(stats['last_updated'])

    def test_path_normalization_with_trailing_slashes(self):
        """Path matching works with various slash formats."""
        files = [
            # ProcessedFile with trailing slash in relative_url
            self._create_processed_file('intro/'),
            self._create_processed_file('/setup'),  # Leading slash
        ]

        stats = self.builder._calculate_directory_stats(
            Path('.'), files, files
        )

        # Both files should be counted
        self.assertEqual(stats['total_pages'], 2)


class TestDirectoryMetadataTemplateTag(TestCase):
    """Test the {% directory_metadata %} template tag."""

    def test_renders_with_full_stats(self):
        """Template tag renders correctly with all stats present."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata %}"
        )

        context = Context({
            'directory_name': 'Guides',
            'directory_stats': {
                'total_pages': 12,
                'direct_pages': 8,
                'subdirectory_count': 3,
                'last_updated': datetime(2025, 12, 9)
            }
        })

        result = template.render(context)

        # No heading in template - just verify stats are present
        self.assertIn('Total pages:', result)
        self.assertIn('12', result)
        self.assertIn('This folder:', result)
        self.assertIn('8', result)
        self.assertIn('Subdirectories:', result)
        self.assertIn('3', result)
        self.assertIn('Last updated:', result)
        self.assertIn('09 Dec 2025', result)

    def test_renders_with_partial_stats(self):
        """Template tag renders correctly with some stats missing."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata %}"
        )

        context = Context({
            'directory_name': 'Guides',
            'directory_stats': {
                'total_pages': 5,
                'direct_pages': 5,
                'subdirectory_count': 0,  # No subdirectories
                'last_updated': None  # No dates
            }
        })

        result = template.render(context)

        # No heading in template - just verify stats are present
        self.assertIn('Total pages:', result)
        self.assertIn('5', result)
        # Subdirectories and Last updated should not appear
        self.assertNotIn('Subdirectories:', result)
        self.assertNotIn('Last updated:', result)

    def test_returns_empty_for_non_directory_page(self):
        """Template tag returns empty string on non-directory pages."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata %}"
        )

        # Regular page context without directory_stats
        context = Context({
            'metadata': {
                'title': 'Regular Page',
                'published': datetime(2025, 12, 1)
            }
        })

        result = template.render(context)

        self.assertEqual(result.strip(), '')

    def test_returns_empty_for_empty_directory(self):
        """Template tag returns empty string for empty directories."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata %}"
        )

        context = Context({
            'directory_name': 'Empty',
            'directory_stats': {
                'total_pages': 0,
                'direct_pages': 0,
                'subdirectory_count': 0,
                'last_updated': None
            }
        })

        result = template.render(context)

        self.assertEqual(result.strip(), '')

    def test_uses_correct_styling_classes(self):
        """Template tag uses spellbook metadata styling classes."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata %}"
        )

        context = Context({
            'directory_stats': {
                'total_pages': 5,
                'direct_pages': 3,
                'subdirectory_count': 1,
                'last_updated': datetime(2025, 12, 1)
            }
        })

        result = template.render(context)

        # Check for metadata styling classes
        # Note: sb-bg-secondary-25 removed - uses CSS .sb-metadata-directory instead
        self.assertIn('sb-metadata', result)


class TestDirectoryMetadataDevView(TestCase):
    """Test {% directory_metadata "for_dev" %} developer view."""

    def test_dev_view_renders_with_developer_info(self):
        """Dev view renders all developer metadata fields."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata 'for_dev' %}"
        )

        context = Context({
            'directory_stats': {
                'total_pages': 5,
                'directory_path': 'docs/getting-started',
                'url_pattern': '/docs/getting-started/',
                'view_name': 'directory_index_docs_getting_started',
                'namespace': 'docs_app',
            }
        })

        result = template.render(context)

        self.assertIn('Developer Metadata', result)
        self.assertIn('docs/getting-started', result)
        self.assertIn('/docs/getting-started/', result)
        self.assertIn('directory_index_docs_getting_started', result)
        self.assertIn('docs_app', result)

    def test_invalid_display_type_returns_error(self):
        """Invalid display_type returns error message."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata 'for_admin' %}"
        )

        context = Context({'directory_stats': {'total_pages': 1}})
        result = template.render(context)

        self.assertIn('Error', result)
        self.assertIn('for_admin', result)

    def test_context_includes_dev_stats(self):
        """_collect_directory_context includes developer stats."""
        from django_spellbook.management.commands.processing.directory_index import DirectoryIndexBuilder
        from django_spellbook.management.commands.processing.file_processor import ProcessedFile
        from unittest.mock import Mock
        from django_spellbook.markdown.context import SpellbookContext

        builder = DirectoryIndexBuilder('test_app', 'docs')

        # Create a processed file
        context = Mock(spec=SpellbookContext)
        context.title = "Test Page"
        context.modified = None
        context.published = None
        pf = ProcessedFile(
            original_path=Path("content/intro.md"),
            html_content="<p>Test</p>",
            template_path=Path("base.html"),
            relative_url="intro",
            context=context
        )

        result = builder._collect_directory_context(
            Path("docs/guides"),
            [pf],
            [pf]
        )

        # Verify dev fields present
        self.assertIn('directory_path', result['directory_stats'])
        self.assertIn('url_pattern', result['directory_stats'])
        self.assertIn('view_name', result['directory_stats'])
        self.assertIn('namespace', result['directory_stats'])

    def test_dev_view_empty_directory_returns_empty(self):
        """Dev view with no stats returns empty string (not error)."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata 'for_dev' %}"
        )

        context = Context({})  # No directory_stats
        result = template.render(context)

        self.assertEqual(result.strip(), '')

    def test_dev_view_root_directory_shows_root(self):
        """Dev view shows '(root)' for root directory."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% directory_metadata 'for_dev' %}"
        )

        context = Context({
            'directory_stats': {
                'total_pages': 3,
                'directory_path': '',  # Root directory
                'url_pattern': '/',
                'view_name': 'directory_index_root_test_app',
                'namespace': 'test_app',
            }
        })

        result = template.render(context)

        self.assertIn('(root)', result)
        self.assertIn('directory_index_root_test_app', result)
        self.assertIn('sb-metadata-dev', result)
        self.assertIn('sb-rounded', result)
        self.assertIn('sb-border', result)
        self.assertIn('sb-metadata-grid', result)


class TestDirectoryContextIntegration(TestCase):
    """Test integration with DirectoryIndexBuilder._collect_directory_context()."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = DirectoryIndexBuilder('test_app', 'docs')

    def _create_processed_file(self, relative_url):
        """Helper to create a ProcessedFile with minimal context."""
        context = Mock(spec=SpellbookContext)
        context.modified = datetime(2025, 12, 1)
        context.published = datetime(2025, 11, 1)
        context.title = f"Page {relative_url}"
        context.tags = []
        context.description = None

        return ProcessedFile(
            original_path=Path(f"content/{relative_url}.md"),
            html_content="<p>Test</p>",
            template_path=Path("templates/base.html"),
            relative_url=relative_url,
            context=context
        )

    def test_context_includes_directory_stats(self):
        """_collect_directory_context() includes directory_stats."""
        files = [
            self._create_processed_file('intro'),
            self._create_processed_file('setup'),
        ]

        all_files = files + [
            self._create_processed_file('advanced/topics'),
        ]

        context = self.builder._collect_directory_context(
            Path('.'), files, all_files
        )

        self.assertIn('directory_stats', context)
        self.assertIn('total_pages', context['directory_stats'])
        self.assertIn('direct_pages', context['directory_stats'])
        self.assertIn('subdirectory_count', context['directory_stats'])
        self.assertIn('last_updated', context['directory_stats'])

    def test_stats_match_directory_content(self):
        """Directory stats accurately reflect directory content."""
        files = [
            self._create_processed_file('intro'),
            self._create_processed_file('setup'),
        ]

        all_files = files + [
            self._create_processed_file('advanced/topics'),
            self._create_processed_file('guides/beginner'),
        ]

        context = self.builder._collect_directory_context(
            Path('.'), files, all_files
        )

        stats = context['directory_stats']

        self.assertEqual(stats['total_pages'], 4)  # All files
        self.assertEqual(stats['direct_pages'], 2)  # Just intro, setup
        self.assertEqual(stats['subdirectory_count'], 2)  # advanced, guides
