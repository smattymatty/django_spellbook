# tests/test_sitemap.py

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from django.test import TestCase

from django_spellbook.management.commands.processing.sitemap import SitemapGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext


class TestSitemapGenerator(TestCase):
    """Tests for the SitemapGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.site_url = "https://example.com"
        self.output_path = Path("/test/sitemap.xml")
        self.generator = SitemapGenerator(self.site_url, self.output_path)

    def _create_processed_file(
        self,
        url_path: str = "test/page",
        is_public: bool = True,
        published: datetime = None,
        modified: datetime = None,
        custom_meta: dict = None,
        namespace: str = "blog"
    ):
        """Helper to create a ProcessedFile with SpellbookContext."""
        context = SpellbookContext(
            title="Test Page",
            url_path=url_path,
            raw_content="Test content",
            is_public=is_public,
            published=published,
            modified=modified,
            custom_meta=custom_meta or {}
        )
        context.namespace = namespace

        return ProcessedFile(
            original_path=Path(f"/test/{url_path}.md"),
            html_content="<h1>Test</h1>",
            template_path=Path(f"/templates/{url_path}.html"),
            relative_url=url_path,
            context=context
        )

    def test_build_entry_public_page(self):
        """Test building entry for a public page."""
        pf = self._create_processed_file(url_path="docs/intro", is_public=True)

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertIsNotNone(entry)
        self.assertEqual(entry['loc'], "https://example.com/docs/intro/")

    def test_build_entry_with_url_prefix(self):
        """Test building entry with URL prefix."""
        pf = self._create_processed_file(url_path="intro", is_public=True)

        entry = self.generator._build_entry(pf, url_prefix="docs")

        self.assertIsNotNone(entry)
        self.assertEqual(entry['loc'], "https://example.com/docs/intro/")

    def test_build_entry_filters_private_pages(self):
        """Test that non-public pages are filtered out."""
        pf = self._create_processed_file(url_path="private", is_public=False)

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertIsNone(entry)

    def test_build_entry_filters_sitemap_excluded(self):
        """Test that pages with sitemap_exclude=True are filtered out."""
        pf = self._create_processed_file(
            url_path="excluded",
            custom_meta={'sitemap_exclude': True}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertIsNone(entry)

    def test_build_entry_with_modified_date(self):
        """Test that modified date is used for lastmod."""
        modified_date = datetime(2025, 12, 8, 10, 30)
        pf = self._create_processed_file(
            url_path="page",
            modified=modified_date
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['lastmod'], "2025-12-08")

    def test_build_entry_with_published_date_fallback(self):
        """Test that published date is used when modified is not set."""
        published_date = datetime(2025, 12, 1, 10, 30)
        pf = self._create_processed_file(
            url_path="page",
            published=published_date,
            modified=None
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['lastmod'], "2025-12-01")

    def test_build_entry_prefers_modified_over_published(self):
        """Test that modified date is preferred over published."""
        published_date = datetime(2025, 12, 1)
        modified_date = datetime(2025, 12, 8)
        pf = self._create_processed_file(
            url_path="page",
            published=published_date,
            modified=modified_date
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['lastmod'], "2025-12-08")

    def test_build_entry_no_dates(self):
        """Test that lastmod is omitted when no dates are available."""
        pf = self._create_processed_file(
            url_path="page",
            published=None,
            modified=None
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertNotIn('lastmod', entry)

    def test_build_entry_with_changefreq(self):
        """Test that changefreq is included from custom_meta."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_changefreq': 'weekly'}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['changefreq'], "weekly")

    def test_build_entry_with_invalid_changefreq(self):
        """Test that invalid changefreq is ignored."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_changefreq': 'invalid'}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertNotIn('changefreq', entry)

    def test_build_entry_with_priority(self):
        """Test that priority is included from custom_meta."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_priority': 0.8}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['priority'], "0.8")

    def test_build_entry_with_invalid_priority_high(self):
        """Test that priority > 1.0 is rejected."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_priority': 1.5}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertNotIn('priority', entry)

    def test_build_entry_with_invalid_priority_low(self):
        """Test that priority < 0.0 is rejected."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_priority': -0.5}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertNotIn('priority', entry)

    def test_build_entry_with_invalid_priority_type(self):
        """Test that non-numeric priority is rejected."""
        pf = self._create_processed_file(
            url_path="page",
            custom_meta={'sitemap_priority': 'high'}
        )

        entry = self.generator._build_entry(pf, url_prefix="")

        self.assertNotIn('priority', entry)

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_write_sitemap(self, mock_mkdir, mock_file):
        """Test writing sitemap to file."""
        entries = [
            {'loc': 'https://example.com/page1/'},
            {'loc': 'https://example.com/page2/', 'lastmod': '2025-12-08'},
        ]

        sitemap_path = self.generator._write_sitemap(entries)

        # Verify file was written
        mock_file.assert_called_once()
        self.assertEqual(sitemap_path, self.output_path)

        # Verify content contains expected XML
        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', written_content)
        self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', written_content)
        self.assertIn('<loc>https://example.com/page1/</loc>', written_content)
        self.assertIn('<loc>https://example.com/page2/</loc>', written_content)
        self.assertIn('<lastmod>2025-12-08</lastmod>', written_content)

    @patch.object(SitemapGenerator, '_write_sitemap')
    def test_generate_with_empty_list(self, mock_write):
        """Test generate with empty processed files list."""
        result = self.generator.generate([], {})

        self.assertIsNone(result)
        mock_write.assert_not_called()

    @patch.object(SitemapGenerator, '_write_sitemap')
    def test_generate_with_all_private_pages(self, mock_write):
        """Test generate when all pages are private."""
        pf1 = self._create_processed_file(url_path="page1", is_public=False)
        pf2 = self._create_processed_file(url_path="page2", is_public=False)

        result = self.generator.generate([pf1, pf2], {'blog': ''})

        self.assertIsNone(result)
        mock_write.assert_not_called()

    @patch.object(SitemapGenerator, '_write_sitemap', return_value=Path('/test/sitemap.xml'))
    def test_generate_with_mixed_pages(self, mock_write):
        """Test generate with mix of public and private pages."""
        pf1 = self._create_processed_file(url_path="public1", is_public=True)
        pf2 = self._create_processed_file(url_path="private", is_public=False)
        pf3 = self._create_processed_file(url_path="public2", is_public=True)

        result = self.generator.generate([pf1, pf2, pf3], {'blog': ''})

        self.assertIsNotNone(result)
        mock_write.assert_called_once()

        # Verify only public pages were passed to _write_sitemap
        entries = mock_write.call_args[0][0]
        self.assertEqual(len(entries), 2)
        self.assertTrue(all('public' in e['loc'] for e in entries))

    @patch.object(SitemapGenerator, '_write_sitemap', return_value=Path('/test/sitemap.xml'))
    def test_generate_with_url_prefix_map(self, mock_write):
        """Test generate with URL prefix mapping."""
        pf1 = self._create_processed_file(url_path="intro", namespace="blog")
        pf2 = self._create_processed_file(url_path="setup", namespace="docs")

        url_prefix_map = {
            'blog': '',
            'docs': 'documentation'
        }

        result = self.generator.generate([pf1, pf2], url_prefix_map)

        # Verify entries were created with correct prefixes
        entries = mock_write.call_args[0][0]
        self.assertEqual(len(entries), 2)

        # Check URLs have correct prefixes
        urls = [e['loc'] for e in entries]
        self.assertIn('https://example.com/intro/', urls)
        self.assertIn('https://example.com/documentation/setup/', urls)

    def test_site_url_trailing_slash_removed(self):
        """Test that trailing slash in site_url is removed."""
        generator = SitemapGenerator("https://example.com/", Path("/test/sitemap.xml"))

        self.assertEqual(generator.site_url, "https://example.com")

    def test_url_construction_with_special_characters(self):
        """Test URL construction handles special characters."""
        pf = self._create_processed_file(url_path="guides/how-to-guide")

        entry = self.generator._build_entry(pf, url_prefix="")

        # URL should be properly formatted (hyphens are valid in URLs)
        self.assertEqual(entry['loc'], "https://example.com/guides/how-to-guide/")

    def test_url_construction_multiple_slashes(self):
        """Test URL construction normalizes multiple slashes."""
        pf = self._create_processed_file(url_path="docs/api")

        entry = self.generator._build_entry(pf, url_prefix="v1")

        # Should not have double slashes
        self.assertEqual(entry['loc'], "https://example.com/v1/docs/api/")
        self.assertNotIn('//', entry['loc'].replace('https://', ''))

    def test_merge_with_no_existing_sitemap(self):
        """Test merge when no sitemap exists."""
        entries = [{'loc': 'https://example.com/page1/'}]

        merged_xml, user_count = self.generator._merge_with_existing(entries)

        self.assertEqual(user_count, 0)
        self.assertIn('<!-- spellbook:start -->', merged_xml)
        self.assertIn('<!-- spellbook:end -->', merged_xml)
        self.assertIn('https://example.com/page1/', merged_xml)

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/user-page/</loc>
  </url>
</urlset>''')
    def test_merge_with_existing_sitemap_no_markers(self, mock_file, mock_exists):
        """Test merge appends to existing sitemap without markers."""
        entries = [{'loc': 'https://example.com/spellbook-page/'}]

        merged_xml, user_count = self.generator._merge_with_existing(entries)

        self.assertEqual(user_count, 1)
        self.assertIn('user-page', merged_xml)
        self.assertIn('spellbook-page', merged_xml)
        self.assertIn('<!-- spellbook:start -->', merged_xml)
        self.assertIn('<!-- spellbook:end -->', merged_xml)

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/user-page/</loc>
  </url>
  <!-- spellbook:start -->
  <url>
    <loc>https://example.com/old-spellbook-page/</loc>
  </url>
  <!-- spellbook:end -->
</urlset>''')
    def test_merge_replaces_content_between_markers(self, mock_file, mock_exists):
        """Test merge replaces content between markers."""
        entries = [{'loc': 'https://example.com/new-spellbook-page/'}]

        merged_xml, user_count = self.generator._merge_with_existing(entries)

        self.assertEqual(user_count, 1)
        self.assertIn('user-page', merged_xml)
        self.assertIn('new-spellbook-page', merged_xml)
        self.assertNotIn('old-spellbook-page', merged_xml)

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/before/</loc>
  </url>
  <!-- spellbook:start -->
  <!-- spellbook:end -->
  <url>
    <loc>https://example.com/after/</loc>
  </url>
</urlset>''')
    def test_merge_preserves_urls_before_and_after_markers(self, mock_file, mock_exists):
        """Test that URLs before and after markers are preserved."""
        entries = [{'loc': 'https://example.com/spellbook/'}]

        merged_xml, user_count = self.generator._merge_with_existing(entries)

        self.assertEqual(user_count, 2)
        self.assertIn('before', merged_xml)
        self.assertIn('after', merged_xml)
        self.assertIn('spellbook', merged_xml)

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- spellbook:end -->
  <!-- spellbook:start -->
</urlset>''')
    def test_merge_handles_malformed_markers(self, mock_file, mock_exists):
        """Test that malformed markers trigger regeneration."""
        entries = [{'loc': 'https://example.com/page/'}]

        merged_xml, user_count = self.generator._merge_with_existing(entries)

        self.assertEqual(user_count, 0)
        self.assertIn('<!-- spellbook:start -->', merged_xml)
        self.assertIn('<!-- spellbook:end -->', merged_xml)

    def test_build_spellbook_section(self):
        """Test building the Spellbook section."""
        entries = [
            {'loc': 'https://example.com/page1/', 'lastmod': '2025-12-08'},
            {'loc': 'https://example.com/page2/', 'changefreq': 'weekly', 'priority': '0.8'}
        ]

        section = self.generator._build_spellbook_section(entries)

        self.assertIn('<url>', section)
        self.assertIn('<loc>https://example.com/page1/</loc>', section)
        self.assertIn('<lastmod>2025-12-08</lastmod>', section)
        self.assertIn('<loc>https://example.com/page2/</loc>', section)
        self.assertIn('<changefreq>weekly</changefreq>', section)
        self.assertIn('<priority>0.8</priority>', section)

    def test_build_spellbook_section_empty(self):
        """Test building empty Spellbook section."""
        section = self.generator._build_spellbook_section([])

        self.assertEqual(section, "")


class TestSitemapGeneratorEdgeCases(TestCase):
    """Test edge cases and error handling for SitemapGenerator."""

    def test_output_path_defaults_to_sitemap_xml(self):
        """Test that output path defaults to sitemap.xml."""
        generator = SitemapGenerator("https://example.com")

        self.assertEqual(generator.output_path, Path("sitemap.xml"))

    def test_valid_changefreq_values(self):
        """Test all valid changefreq values are accepted."""
        valid_freqs = ['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']
        generator = SitemapGenerator("https://example.com")

        for freq in valid_freqs:
            context = SpellbookContext(
                title="Test",
                url_path="test",
                raw_content="content",
                custom_meta={'sitemap_changefreq': freq}
            )
            context.namespace = "test"

            pf = ProcessedFile(
                original_path=Path("/test.md"),
                html_content="<p>test</p>",
                template_path=Path("/templates/test.html"),
                relative_url="test",
                context=context
            )

            entry = generator._build_entry(pf, url_prefix="")

            self.assertEqual(entry['changefreq'], freq.lower())

    def test_changefreq_case_insensitive(self):
        """Test that changefreq is case-insensitive."""
        context = SpellbookContext(
            title="Test",
            url_path="test",
            raw_content="content",
            custom_meta={'sitemap_changefreq': 'WEEKLY'}
        )
        context.namespace = "test"

        pf = ProcessedFile(
            original_path=Path("/test.md"),
            html_content="<p>test</p>",
            template_path=Path("/templates/test.html"),
            relative_url="test",
            context=context
        )

        generator = SitemapGenerator("https://example.com")
        entry = generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['changefreq'], "weekly")

    def test_priority_formatted_to_one_decimal(self):
        """Test that priority is formatted to one decimal place."""
        context = SpellbookContext(
            title="Test",
            url_path="test",
            raw_content="content",
            custom_meta={'sitemap_priority': 0.5}
        )
        context.namespace = "test"

        pf = ProcessedFile(
            original_path=Path("/test.md"),
            html_content="<p>test</p>",
            template_path=Path("/templates/test.html"),
            relative_url="test",
            context=context
        )

        generator = SitemapGenerator("https://example.com")
        entry = generator._build_entry(pf, url_prefix="")

        self.assertEqual(entry['priority'], "0.5")

    def test_url_path_with_leading_slash(self):
        """Test URL construction with leading slash in url_path."""
        context = SpellbookContext(
            title="Test",
            url_path="/docs/intro",  # Leading slash
            raw_content="content"
        )
        context.namespace = "test"

        pf = ProcessedFile(
            original_path=Path("/test.md"),
            html_content="<p>test</p>",
            template_path=Path("/templates/test.html"),
            relative_url="docs/intro",
            context=context
        )

        generator = SitemapGenerator("https://example.com")
        entry = generator._build_entry(pf, url_prefix="")

        # Leading slash should be normalized
        self.assertEqual(entry['loc'], "https://example.com/docs/intro/")
