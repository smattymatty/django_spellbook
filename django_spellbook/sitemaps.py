# django_spellbook/sitemaps.py

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from django.contrib.sitemaps import Sitemap
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)


class SpellbookSitemap(Sitemap):
    """
    Django Sitemap class for Spellbook-generated pages.

    This class integrates with Django's sitemap framework to dynamically
    generate sitemap entries from Spellbook-processed markdown files.

    Usage in user's sitemaps.py:
        from django_spellbook.sitemaps import SpellbookSitemap

        sitemaps = {
            'spellbook': SpellbookSitemap,
        }

    Or with specific apps:
        sitemaps = {
            'spellbook': SpellbookSitemap(app_names=['docs', 'blog']),
        }

    Then in urls.py:
        from django.contrib.sitemaps.views import sitemap
        from .sitemaps import sitemaps

        urlpatterns = [
            path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
        ]
    """

    changefreq = 'weekly'
    priority = 0.5

    def __init__(self, app_names: Optional[List[str]] = None):
        """
        Initialize SpellbookSitemap.

        Args:
            app_names: List of app names to include.
                       If None, discovers all apps with manifests.
        """
        self.app_names = app_names
        super().__init__()

    def items(self):
        """Return all pages from all Spellbook manifests."""
        pages = []

        for manifest in self._load_manifests():
            pages.extend(manifest.get('pages', []))

        return pages

    def location(self, item):
        """Return the URL path for a page."""
        return item['path']

    def lastmod(self, item):
        """Return the last modified date for a page."""
        if item.get('lastmod'):
            try:
                # Parse ISO date string (YYYY-MM-DD)
                return datetime.fromisoformat(item['lastmod'])
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid lastmod date '{item.get('lastmod')}': {e}")
                return None
        return None

    def priority(self, item):
        """Return priority for item, or None to use class default."""
        return item.get('priority')

    def changefreq(self, item):
        """Return changefreq for item, or None to use class default."""
        return item.get('changefreq')

    def _load_manifests(self) -> List[dict]:
        """Load all spellbook_manifest.json files."""
        manifests = []

        app_names = self.app_names or self._discover_spellbook_apps()

        for app_name in app_names:
            try:
                app_config = apps.get_app_config(app_name)
                manifest_path = Path(app_config.path) / 'spellbook_manifest.json'

                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        manifests.append(manifest)
                        logger.debug(f"Loaded manifest from {app_name}: {len(manifest.get('pages', []))} pages")
                else:
                    logger.debug(f"No manifest found for app {app_name} at {manifest_path}")
            except LookupError:
                logger.warning(f"App '{app_name}' not found in INSTALLED_APPS")
                continue
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error loading manifest from {app_name}: {e}")
                continue

        return manifests

    def _discover_spellbook_apps(self) -> List[str]:
        """Find all apps that should have Spellbook manifests."""
        # Check SPELLBOOK_MD_APP setting
        configured_apps = getattr(settings, 'SPELLBOOK_MD_APP', [])

        # Handle single string or list
        if isinstance(configured_apps, str):
            configured_apps = [configured_apps]

        return configured_apps
