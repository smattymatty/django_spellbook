# django_spellbook/management/commands/processing/sitemap.py

import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom

from django_spellbook.management.commands.processing.file_processor import ProcessedFile

logger = logging.getLogger(__name__)

# Marker comments to identify Spellbook-managed URLs in sitemap.xml
SPELLBOOK_SITEMAP_START = "<!-- spellbook:start -->"
SPELLBOOK_SITEMAP_END = "<!-- spellbook:end -->"


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

    def _merge_with_existing(self, spellbook_entries: List[Dict[str, str]]) -> tuple[str, int]:
        """
        Merge Spellbook-generated URLs with existing sitemap.xml.

        Preserves user-defined URLs outside of spellbook markers.
        Replaces everything between <!-- spellbook:start --> and <!-- spellbook:end -->.

        Args:
            spellbook_entries: List of Spellbook-generated sitemap entries

        Returns:
            Tuple of (merged XML string, count of preserved user URLs)
        """
        output_path = Path(self.output_path)

        # Check if sitemap exists
        if not output_path.exists():
            # No existing sitemap, create new one with markers
            return self._create_sitemap_with_markers(spellbook_entries), 0

        # Read existing sitemap
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read existing sitemap, creating new one: {e}")
            return self._create_sitemap_with_markers(spellbook_entries), 0

        # Check for markers
        start_marker_pos = existing_content.find(SPELLBOOK_SITEMAP_START)
        end_marker_pos = existing_content.find(SPELLBOOK_SITEMAP_END)

        if start_marker_pos == -1 or end_marker_pos == -1:
            # No markers found, append Spellbook section at end
            return self._append_spellbook_section(existing_content, spellbook_entries)

        if end_marker_pos <= start_marker_pos:
            # Malformed markers, warn and regenerate
            logger.warning("Malformed sitemap markers detected, regenerating sitemap")
            return self._create_sitemap_with_markers(spellbook_entries), 0

        # Extract user URLs (before start marker and after end marker)
        before_marker = existing_content[:start_marker_pos].strip()
        after_marker = existing_content[end_marker_pos + len(SPELLBOOK_SITEMAP_END):].strip()

        # Count user URLs
        user_url_count = before_marker.count('<url>') + after_marker.count('<url>')

        # Build Spellbook section
        spellbook_section = self._build_spellbook_section(spellbook_entries)

        # Merge: before + markers + spellbook URLs + after
        # Need to handle the urlset tags properly
        merged = self._reconstruct_sitemap(before_marker, spellbook_section, after_marker)

        return merged, user_url_count

    def _create_sitemap_with_markers(self, entries: List[Dict[str, str]]) -> str:
        """Create a new sitemap with Spellbook markers."""
        # Create XML structure
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        xml_string = ET.tostring(urlset, encoding='unicode')

        # Build Spellbook section
        spellbook_section = self._build_spellbook_section(entries)

        # Insert markers into empty urlset
        # We need to add the spellbook section inside the urlset tags
        opening = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        closing = '</urlset>'

        return f"{opening}\n  {SPELLBOOK_SITEMAP_START}\n{spellbook_section}  {SPELLBOOK_SITEMAP_END}\n{closing}"

    def _append_spellbook_section(self, existing_content: str, entries: List[Dict[str, str]]) -> tuple[str, int]:
        """Append Spellbook section to existing sitemap without markers."""
        # Count existing user URLs
        user_url_count = existing_content.count('<url>')

        # Find closing </urlset> tag
        closing_tag_pos = existing_content.rfind('</urlset>')

        if closing_tag_pos == -1:
            logger.warning("Invalid sitemap XML, regenerating")
            return self._create_sitemap_with_markers(entries), 0

        # Build Spellbook section
        spellbook_section = self._build_spellbook_section(entries)

        # Insert before closing tag
        before_closing = existing_content[:closing_tag_pos].rstrip()
        after_closing = existing_content[closing_tag_pos:]

        merged = f"{before_closing}\n  {SPELLBOOK_SITEMAP_START}\n{spellbook_section}  {SPELLBOOK_SITEMAP_END}\n{after_closing}"

        return merged, user_url_count

    def _reconstruct_sitemap(self, before: str, spellbook_section: str, after: str) -> str:
        """Reconstruct sitemap from parts."""
        # before contains everything up to the start marker (including opening tags)
        # after contains everything after the end marker (including closing tags)

        # We need to handle the case where before/after might contain partial content
        # The safest approach is to ensure we have proper XML structure

        # Find the opening urlset tag in before
        if '<urlset' in before:
            # Keep everything including the urlset opening
            pass
        else:
            # No urlset in before, add it
            before = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + before

        # Ensure after contains closing tag
        if '</urlset>' not in after:
            after = after + '\n</urlset>'

        # Combine parts
        return f"{before}\n  {SPELLBOOK_SITEMAP_START}\n{spellbook_section}  {SPELLBOOK_SITEMAP_END}\n{after}"

    def _build_spellbook_section(self, entries: List[Dict[str, str]]) -> str:
        """Build the Spellbook-managed section of the sitemap."""
        if not entries:
            return ""

        lines = []
        for entry_data in entries:
            lines.append("  <url>")
            lines.append(f"    <loc>{entry_data['loc']}</loc>")

            if 'lastmod' in entry_data:
                lines.append(f"    <lastmod>{entry_data['lastmod']}</lastmod>")

            if 'changefreq' in entry_data:
                lines.append(f"    <changefreq>{entry_data['changefreq']}</changefreq>")

            if 'priority' in entry_data:
                lines.append(f"    <priority>{entry_data['priority']}</priority>")

            lines.append("  </url>")

        return '\n'.join(lines) + '\n'

    def _write_sitemap(self, entries: List[Dict[str, str]]) -> Path:
        """
        Write XML sitemap to file, merging with existing content.

        Args:
            entries: List of sitemap entry dictionaries

        Returns:
            Path to written sitemap file
        """
        # Merge with existing sitemap
        merged_xml, user_url_count = self._merge_with_existing(entries)

        # Write to file
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(merged_xml)

        # Log merge info
        if user_url_count > 0:
            logger.info(f"Merged {len(entries)} Spellbook URLs into existing sitemap (preserved {user_url_count} user URLs)")
        else:
            logger.info(f"Generated sitemap with {len(entries)} URLs")

        return output_path
