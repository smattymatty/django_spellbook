# tests/test_django_sitemaps.py

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from django.test import TestCase

from django_spellbook.management.commands.processing.manifest import ManifestGenerator
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.sitemaps import SpellbookSitemap


class TestManifestGeneration(TestCase):
    """Test manifest file generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = ManifestGenerator()
        self.output_dir = Path("/test/output")
        self.app_name = "test_app"

    def _create_processed_file(
        self,
        url_path: str = "test/page",
        is_public: bool = True,
        published: datetime = None,
        modified: datetime = None,
        title: str = "Test Page",
        namespace: str = "test_app",
        sitemap_priority: float = None,
        sitemap_changefreq: str = None,
        sitemap_exclude: bool = False
    ):
        """Helper to create a ProcessedFile with SpellbookContext."""
        context = SpellbookContext(
            title=title,
            url_path=url_path,
            raw_content="Test content",
            is_public=is_public,
            published=published,
            modified=modified,
            sitemap_priority=sitemap_priority,
            sitemap_changefreq=sitemap_changefreq,
            sitemap_exclude=sitemap_exclude
        )
        context.namespace = namespace

        return ProcessedFile(
            original_path=Path(f"/test/{url_path}.md"),
            html_content="<h1>Test</h1>",
            template_path=Path(f"/templates/{url_path}.html"),
            relative_url=url_path,
            context=context
        )

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_created(self, mock_file, mock_mkdir):
        """Manifest file created during generation."""
        pf = self._create_processed_file()

        manifest_path = self.generator.generate(
            processed_files=[pf],
            app_name=self.app_name,
            output_dir=self.output_dir
        )

        # Verify file was created
        self.assertIsNotNone(manifest_path)
        self.assertEqual(manifest_path.name, 'spellbook_manifest.json')
        mock_file.assert_called_once()

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_contains_pages(self, mock_file, mock_mkdir):
        """All public pages included in manifest."""
        pf1 = self._create_processed_file(url_path="page1", title="Page 1")
        pf2 = self._create_processed_file(url_path="page2", title="Page 2")

        manifest_path = self.generator.generate(
            processed_files=[pf1, pf2],
            app_name=self.app_name,
            output_dir=self.output_dir
        )

        # Get written content
        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )

        manifest = json.loads(written_content)

        self.assertEqual(len(manifest['pages']), 2)
        self.assertEqual(manifest['app_name'], self.app_name)
        self.assertIn('generated_at', manifest)

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_excludes_private(self, mock_file, mock_mkdir):
        """Pages with is_public: false excluded."""
        pf1 = self._create_processed_file(url_path="public", is_public=True)
        pf2 = self._create_processed_file(url_path="private", is_public=False)

        manifest_path = self.generator.generate(
            processed_files=[pf1, pf2],
            app_name=self.app_name,
            output_dir=self.output_dir
        )

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )

        manifest = json.loads(written_content)

        self.assertEqual(len(manifest['pages']), 1)
        self.assertEqual(manifest['pages'][0]['path'], '/public/')

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_lastmod(self, mock_file, mock_mkdir):
        """lastmod uses modified or published date."""
        modified_date = datetime(2025, 12, 8, 10, 30)
        pf = self._create_processed_file(modified=modified_date)

        manifest_path = self.generator.generate(
            processed_files=[pf],
            app_name=self.app_name,
            output_dir=self.output_dir
        )

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )

        manifest = json.loads(written_content)

        self.assertEqual(manifest['pages'][0]['lastmod'], '2025-12-08')

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_with_url_prefix(self, mock_file, mock_mkdir):
        """URL prefix is applied to paths."""
        pf = self._create_processed_file(url_path="guide")

        manifest_path = self.generator.generate(
            processed_files=[pf],
            app_name=self.app_name,
            output_dir=self.output_dir,
            url_prefix="docs"
        )

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )

        manifest = json.loads(written_content)

        self.assertEqual(manifest['pages'][0]['path'], '/docs/guide/')

    def test_generate_with_empty_list(self):
        """Test generate with empty processed files list."""
        result = self.generator.generate([], self.app_name, self.output_dir)

        self.assertIsNone(result)

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_with_all_private_pages(self, mock_file, mock_mkdir):
        """Test generate when all pages are private."""
        pf1 = self._create_processed_file(url_path="page1", is_public=False)
        pf2 = self._create_processed_file(url_path="page2", is_public=False)

        result = self.generator.generate([pf1, pf2], self.app_name, self.output_dir)

        self.assertIsNone(result)
        mock_file.assert_not_called()

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_includes_priority(self, mock_file, mock_mkdir):
        """Priority from context included in manifest."""
        pf = self._create_processed_file(url_path="page", sitemap_priority=0.9)

        self.generator.generate([pf], self.app_name, self.output_dir)

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        manifest = json.loads(written_content)

        self.assertEqual(manifest['pages'][0]['priority'], 0.9)

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_includes_changefreq(self, mock_file, mock_mkdir):
        """Changefreq from context included in manifest."""
        pf = self._create_processed_file(url_path="page", sitemap_changefreq="daily")

        self.generator.generate([pf], self.app_name, self.output_dir)

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        manifest = json.loads(written_content)

        self.assertEqual(manifest['pages'][0]['changefreq'], 'daily')

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_excludes_sitemap_exclude(self, mock_file, mock_mkdir):
        """Pages with sitemap_exclude=true are filtered out."""
        pf = self._create_processed_file(url_path="excluded", sitemap_exclude=True)

        result = self.generator.generate([pf], self.app_name, self.output_dir)

        # Should return None because all pages are excluded
        self.assertIsNone(result)
        mock_file.assert_not_called()

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_manifest_mixed_sitemap_exclude(self, mock_file, mock_mkdir):
        """Only non-excluded pages included in manifest."""
        pf1 = self._create_processed_file(url_path="included", sitemap_exclude=False)
        pf2 = self._create_processed_file(url_path="excluded", sitemap_exclude=True)

        self.generator.generate([pf1, pf2], self.app_name, self.output_dir)

        written_content = ''.join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        manifest = json.loads(written_content)

        self.assertEqual(len(manifest['pages']), 1)
        self.assertEqual(manifest['pages'][0]['path'], '/included/')


class TestSpellbookSitemap(TestCase):
    """Test Django Sitemap integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.manifest_data = {
            'generated_at': '2025-12-08T14:32:00Z',
            'app_name': 'test_app',
            'pages': [
                {
                    'path': '/docs/guide/',
                    'title': 'User Guide',
                    'lastmod': '2025-12-08'
                },
                {
                    'path': '/docs/tutorial/',
                    'title': 'Tutorial',
                    'lastmod': '2025-12-07'
                }
            ]
        }

    def test_items_returns_pages(self):
        """items() returns all pages from manifest."""
        sitemap = SpellbookSitemap(app_names=['test_app'])

        with patch.object(sitemap, '_load_manifests', return_value=[self.manifest_data]):
            items = sitemap.items()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['path'], '/docs/guide/')
        self.assertEqual(items[1]['path'], '/docs/tutorial/')

    def test_location(self):
        """location() returns correct path."""
        sitemap = SpellbookSitemap()
        item = {'path': '/docs/guide/'}

        location = sitemap.location(item)

        self.assertEqual(location, '/docs/guide/')

    def test_lastmod(self):
        """lastmod() parses date correctly."""
        sitemap = SpellbookSitemap()
        item = {'lastmod': '2025-12-08'}

        lastmod = sitemap.lastmod(item)

        self.assertIsInstance(lastmod, datetime)
        self.assertEqual(lastmod.year, 2025)
        self.assertEqual(lastmod.month, 12)
        self.assertEqual(lastmod.day, 8)

    def test_lastmod_missing(self):
        """lastmod() returns None when date is missing."""
        sitemap = SpellbookSitemap()
        item = {}

        lastmod = sitemap.lastmod(item)

        self.assertIsNone(lastmod)

    def test_lastmod_invalid(self):
        """lastmod() returns None for invalid date."""
        sitemap = SpellbookSitemap()
        item = {'lastmod': 'invalid-date'}

        lastmod = sitemap.lastmod(item)

        self.assertIsNone(lastmod)

    def test_multi_app(self):
        """Aggregates pages from multiple app manifests."""
        manifest1 = {
            'app_name': 'app1',
            'pages': [{'path': '/app1/page/', 'title': 'App1 Page'}]
        }
        manifest2 = {
            'app_name': 'app2',
            'pages': [{'path': '/app2/page/', 'title': 'App2 Page'}]
        }

        sitemap = SpellbookSitemap(app_names=['app1', 'app2'])

        with patch.object(sitemap, '_load_manifests', return_value=[manifest1, manifest2]):
            items = sitemap.items()

        self.assertEqual(len(items), 2)
        paths = [item['path'] for item in items]
        self.assertIn('/app1/page/', paths)
        self.assertIn('/app2/page/', paths)

    @patch('django.apps.apps.get_app_config')
    @patch('pathlib.Path.exists', return_value=False)
    def test_missing_manifest(self, mock_exists, mock_get_app):
        """Gracefully handles missing manifest file."""
        mock_app_config = MagicMock()
        mock_app_config.path = '/test/app'
        mock_get_app.return_value = mock_app_config

        sitemap = SpellbookSitemap(app_names=['test_app'])
        items = sitemap.items()

        # Should return empty list without error
        self.assertEqual(len(items), 0)

    @patch('django.apps.apps.get_app_config')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"pages": [{"path": "/test/"}]}')
    def test_load_manifests_success(self, mock_file, mock_exists, mock_get_app):
        """_load_manifests loads manifest successfully."""
        mock_app_config = MagicMock()
        mock_app_config.path = '/test/app'
        mock_get_app.return_value = mock_app_config

        sitemap = SpellbookSitemap(app_names=['test_app'])
        manifests = sitemap._load_manifests()

        self.assertEqual(len(manifests), 1)
        self.assertIn('pages', manifests[0])

    @patch('django_spellbook.sitemaps.settings')
    def test_discover_spellbook_apps_single_string(self, mock_settings):
        """_discover_spellbook_apps handles single string setting."""
        mock_settings.SPELLBOOK_MD_APP = 'test_app'

        sitemap = SpellbookSitemap()
        apps = sitemap._discover_spellbook_apps()

        self.assertEqual(apps, ['test_app'])

    @patch('django_spellbook.sitemaps.settings')
    def test_discover_spellbook_apps_list(self, mock_settings):
        """_discover_spellbook_apps handles list setting."""
        mock_settings.SPELLBOOK_MD_APP = ['app1', 'app2']

        sitemap = SpellbookSitemap()
        apps = sitemap._discover_spellbook_apps()

        self.assertEqual(apps, ['app1', 'app2'])

    @patch('django_spellbook.sitemaps.settings')
    def test_discover_spellbook_apps_empty(self, mock_settings):
        """_discover_spellbook_apps handles missing setting."""
        mock_settings.SPELLBOOK_MD_APP = []

        sitemap = SpellbookSitemap()
        apps = sitemap._discover_spellbook_apps()

        self.assertEqual(apps, [])

    def test_priority_from_item(self):
        """priority() returns item priority."""
        sitemap = SpellbookSitemap()
        item = {'path': '/test/', 'priority': 0.8}

        self.assertEqual(sitemap.priority(item), 0.8)

    def test_priority_missing(self):
        """priority() returns None for missing priority (uses class default)."""
        sitemap = SpellbookSitemap()
        item = {'path': '/test/'}

        self.assertIsNone(sitemap.priority(item))

    def test_changefreq_from_item(self):
        """changefreq() returns item changefreq."""
        sitemap = SpellbookSitemap()
        item = {'path': '/test/', 'changefreq': 'daily'}

        self.assertEqual(sitemap.changefreq(item), 'daily')

    def test_changefreq_missing(self):
        """changefreq() returns None for missing changefreq (uses class default)."""
        sitemap = SpellbookSitemap()
        item = {'path': '/test/'}

        self.assertIsNone(sitemap.changefreq(item))
