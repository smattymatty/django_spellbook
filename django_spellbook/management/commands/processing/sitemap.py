# django_spellbook/management/commands/processing/sitemap.py

import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom

from django_spellbook.management.commands.processing.file_processor import ProcessedFile

logger = logging.getLogger(__name__)


class SitemapGenerator:
    """
    Generates sitemap.xml from processed markdown files.

    Sitemap format follows the sitemaps.org protocol:
    https://www.sitemaps.org/protocol.html

    Features:
    - Automatic URL generation from ProcessedFile metadata
    - Filters non-public pages (is_public=False)
    - Supports sitemap_exclude frontmatter flag
    - Uses modified/published dates for <lastmod>
    - Per-page changefreq and priority support
    - XML escaping for special characters
    """

    def __init__(self, site_url: str, output_path: Optional[Path] = None):
        """
        Initialize sitemap generator.

        Args:
            site_url: Base URL of the site (e.g., 'https://example.com')
            output_path: Path to write sitemap.xml (defaults to project root)
        """
        self.site_url = site_url.rstrip('/')
        self.output_path = output_path or Path('sitemap.xml')

    def generate(
        self,
        processed_files: List[ProcessedFile],
        url_prefix_map: Dict[str, str]
    ) -> Optional[Path]:
        """
        Generate sitemap.xml from processed files.

        Args:
            processed_files: List of all processed markdown files
            url_prefix_map: Maps content_app to url_prefix

        Returns:
            Path to generated sitemap, or None if no public pages
        """
        if not processed_files:
            logger.warning("No processed files to generate sitemap from")
            return None

        logger.info(f"Generating sitemap from {len(processed_files)} processed files")

        # Build sitemap entries
        entries = []
        for pf in processed_files:
            # Get URL prefix for this file's content app
            url_prefix = url_prefix_map.get(pf.context.namespace, '')

            entry = self._build_entry(pf, url_prefix)
            if entry:
                entries.append(entry)

        if not entries:
            logger.warning("No public pages found, skipping sitemap generation")
            return None

        # Write sitemap
        sitemap_path = self._write_sitemap(entries)
        logger.info(f"Generated sitemap with {len(entries)} URLs at {sitemap_path}")

        return sitemap_path

    def _build_entry(
        self,
        pf: ProcessedFile,
        url_prefix: str
    ) -> Optional[Dict[str, str]]:
        """
        Build sitemap entry from ProcessedFile.

        Args:
            pf: Processed markdown file
            url_prefix: URL prefix for this file's content app

        Returns:
            Dictionary with sitemap entry data, or None if filtered
        """
        # Skip non-public pages
        if not pf.context.is_public:
            logger.debug(f"Skipping non-public page: {pf.relative_url}")
            return None

        # Skip pages with sitemap_exclude=True
        if pf.context.custom_meta.get('sitemap_exclude'):
            logger.debug(f"Skipping excluded page: {pf.relative_url}")
            return None

        # Build full URL
        url_parts = [self.site_url]

        if url_prefix:
            url_parts.append(url_prefix)

        url_parts.append(pf.context.url_path)

        # Construct URL with proper slashes
        loc = '/'.join(part.strip('/') for part in url_parts if part) + '/'

        # Build entry
        entry = {'loc': loc}

        # Add lastmod (prefer modified, fallback to published)
        lastmod = pf.context.modified or pf.context.published
        if lastmod:
            # Format as ISO date (YYYY-MM-DD)
            if isinstance(lastmod, datetime):
                entry['lastmod'] = lastmod.strftime('%Y-%m-%d')
            else:
                entry['lastmod'] = str(lastmod)

        # Add changefreq if specified
        changefreq = pf.context.custom_meta.get('sitemap_changefreq')
        if changefreq:
            valid_freqs = ['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']
            if changefreq.lower() in valid_freqs:
                entry['changefreq'] = changefreq.lower()
            else:
                logger.warning(f"Invalid changefreq '{changefreq}' for {pf.relative_url}")

        # Add priority if specified
        priority = pf.context.custom_meta.get('sitemap_priority')
        if priority is not None:
            try:
                priority_float = float(priority)
                if 0.0 <= priority_float <= 1.0:
                    entry['priority'] = f"{priority_float:.1f}"
                else:
                    logger.warning(f"Invalid priority '{priority}' for {pf.relative_url} (must be 0.0-1.0)")
            except (ValueError, TypeError):
                logger.warning(f"Invalid priority '{priority}' for {pf.relative_url} (must be numeric)")

        return entry

    def _write_sitemap(self, entries: List[Dict[str, str]]) -> Path:
        """
        Write XML sitemap to file.

        Args:
            entries: List of sitemap entry dictionaries

        Returns:
            Path to written sitemap file
        """
        # Create XML structure
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        for entry_data in entries:
            url = ET.SubElement(urlset, 'url')

            # Add loc (required)
            loc = ET.SubElement(url, 'loc')
            loc.text = entry_data['loc']

            # Add optional elements
            if 'lastmod' in entry_data:
                lastmod = ET.SubElement(url, 'lastmod')
                lastmod.text = entry_data['lastmod']

            if 'changefreq' in entry_data:
                changefreq = ET.SubElement(url, 'changefreq')
                changefreq.text = entry_data['changefreq']

            if 'priority' in entry_data:
                priority = ET.SubElement(url, 'priority')
                priority.text = entry_data['priority']

        # Convert to pretty-printed XML
        xml_string = ET.tostring(urlset, encoding='unicode')

        # Use minidom for pretty printing
        dom = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{xml_string}')
        pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)

        # Write to file
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

        return output_path
