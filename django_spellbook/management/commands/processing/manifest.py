# django_spellbook/management/commands/processing/manifest.py

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from django_spellbook.management.commands.processing.file_processor import ProcessedFile

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """
    Generates a manifest of processed pages for runtime consumption.

    The manifest file enables Django's sitemap framework to discover
    Spellbook-generated pages at request time, even though pages are
    processed at build time.

    Manifest format:
    {
        "generated_at": "2025-12-08T14:32:00Z",
        "app_name": "docs",
        "pages": [
            {
                "path": "/docs/guide/",
                "lastmod": "2025-12-08",
                "title": "User Guide"
            }
        ]
    }
    """

    MANIFEST_FILENAME = 'spellbook_manifest.json'

    def generate(
        self,
        processed_files: List[ProcessedFile],
        app_name: str,
        output_dir: Path,
        url_prefix: str = ''
    ) -> Optional[Path]:
        """
        Write manifest to app directory.

        Args:
            processed_files: List of processed markdown files
            app_name: Django app name
            output_dir: Directory to write manifest to
            url_prefix: URL prefix for pages (e.g., 'docs')

        Returns:
            Path to generated manifest, or None if no public pages
        """
        if not processed_files:
            logger.warning("No processed files to generate manifest from")
            return None

        logger.info(f"Generating manifest from {len(processed_files)} processed files")

        # Build manifest structure
        manifest = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'app_name': app_name,
            'pages': []
        }

        for pf in processed_files:
            # Skip non-public pages
            if not pf.context.is_public:
                continue

            # Build page entry
            page_entry = self._build_page_entry(pf, url_prefix)
            if page_entry:
                # Skip pages with sitemap_exclude flag
                if not page_entry.get('sitemap_exclude', False):
                    # Remove the flag before adding to manifest (internal use only)
                    page_entry.pop('sitemap_exclude', None)
                    manifest['pages'].append(page_entry)

        if not manifest['pages']:
            logger.warning("No public pages found, skipping manifest generation")
            return None

        # Write manifest
        manifest_path = self._write_manifest(manifest, output_dir)
        logger.info(f"Generated manifest with {len(manifest['pages'])} pages at {manifest_path}")

        return manifest_path

    def _build_page_entry(self, pf: ProcessedFile, url_prefix: str) -> Optional[dict]:
        """
        Build manifest entry for a page.

        Args:
            pf: Processed markdown file
            url_prefix: URL prefix for this page

        Returns:
            Dictionary with page data, or None if filtered
        """
        # Build full path
        path_parts = []

        if url_prefix:
            path_parts.append(url_prefix)

        path_parts.append(pf.context.url_path)

        # Construct path with proper slashes
        path = '/' + '/'.join(part.strip('/') for part in path_parts if part) + '/'

        # Build entry
        entry = {
            'path': path,
            'title': pf.context.title or ''
        }

        # Add lastmod (prefer modified, fallback to published)
        lastmod = pf.context.modified or pf.context.published
        if lastmod:
            # Format as ISO date (YYYY-MM-DD)
            if isinstance(lastmod, datetime):
                entry['lastmod'] = lastmod.strftime('%Y-%m-%d')
            else:
                entry['lastmod'] = str(lastmod)

        # Add sitemap control
        if pf.context.sitemap_priority is not None:
            entry['priority'] = float(pf.context.sitemap_priority)

        if pf.context.sitemap_changefreq:
            entry['changefreq'] = pf.context.sitemap_changefreq

        if pf.context.sitemap_exclude:
            entry['sitemap_exclude'] = True

        return entry

    def _write_manifest(self, manifest: dict, output_dir: Path) -> Path:
        """
        Write manifest JSON to file.

        Args:
            manifest: Manifest dictionary
            output_dir: Directory to write to

        Returns:
            Path to written manifest file
        """
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write manifest
        manifest_path = output_dir / self.MANIFEST_FILENAME

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest_path
