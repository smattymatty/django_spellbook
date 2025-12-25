# django_spellbook/markdown/frontmatter.py
import yaml
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from django_spellbook.utils import remove_leading_dash, titlefy
from .context import SpellbookContext

# --- Define potential keys for dates ---
# Order matters: first found key will be used.
PUBLISHED_KEYS = ['published', 'published_at', 'date', 'created', 'created_at']
MODIFIED_KEYS = ['modified', 'modified_at', 'updated', 'updated_at']

# --- Keys to exclude from custom_meta ---
# Includes standard keys and the date aliases we might consume
RESERVED_META_KEYS = ['title', 'is_public', 'tags', 'author', 'prev', 'next', 'sitemap_priority', 'sitemap_changefreq', 'sitemap_exclude'] + PUBLISHED_KEYS + MODIFIED_KEYS
# Make the check case-insensitive later for robustness
LOWERCASE_RESERVED_META_KEYS = [k.lower() for k in RESERVED_META_KEYS]

class FrontMatterParser:
    def __init__(self, content: str, file_path: Path):
        self.content = content
        self.file_path = file_path
        self.raw_content = ""
        # Ensure metadata is always a dict initially
        self.metadata: Dict[str, Any] = {}
        self._parse()

    def _parse(self):
        """Parse front matter and content"""
        if self.content.startswith('---'):
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                try:
                    yaml_content = parts[1] # No need for encode/decode dance if source is utf-8
                    loaded_meta = yaml.safe_load(yaml_content)
                    # Ensure metadata is always a dict, even if YAML is null/empty
                    self.metadata = loaded_meta if isinstance(loaded_meta, dict) else {}
                    self.raw_content = parts[2].strip()
                except (yaml.YAMLError, AttributeError) as e:
                    print(f"Warning: Could not parse YAML frontmatter in {self.file_path}: {e}. Treating as no frontmatter.")
                    # Fallback: keep metadata empty, use entire content
                    self.metadata = {}
                    self.raw_content = self.content
            else: # Less than 3 parts means invalid frontmatter format
                print(f"Warning: Invalid frontmatter format (not enough '---') in {self.file_path}. Treating as no frontmatter.")
                self.metadata = {}
                self.raw_content = self.content
        else: # No starting '---'
            self.metadata = {}
            self.raw_content = self.content

    def _parse_date_from_metadata(self, keys_to_check: List[str]) -> Optional[datetime]:
        """
        Attempts to find and parse a date from metadata using a list of keys.
        Returns the first valid datetime found, or None.
        """
        for key in keys_to_check:
            value = self.metadata.get(key)
            if value:
                # Handle datetime objects directly (parsed by PyYAML)
                if isinstance(value, datetime):
                    return value
                # Handle date objects (parsed by PyYAML), convert to datetime
                if isinstance(value, date):
                    return datetime.combine(value, datetime.min.time())
                # Attempt to parse from string (e.g., ISO format YYYY-MM-DD)
                if isinstance(value, str):
                    try:
                        # Be relatively strict first with ISO format
                        return datetime.fromisoformat(value.strip())
                    except ValueError:
                        # Try a common format as fallback
                        try:
                            return datetime.strptime(value.strip(), '%Y-%m-%d')
                        except ValueError:
                            print(f"Warning: Could not parse date string '{value}' for key '{key}' in {self.file_path}. Supported formats: ISO (YYYY-MM-DDTHH:MM:SS), YYYY-MM-DD.")
                            continue # Try next key

                # Log if value is present but not a recognizable type
                print(f"Warning: Unexpected type '{type(value)}' for date key '{key}' in {self.file_path}. Skipping.")


        return None # Return None if no valid date found across all keys


    def get_context(self, url_path: str) -> SpellbookContext:
        split_path = url_path.split('/')
        clean_path = [remove_leading_dash(part) for part in split_path]
        clean_url = "/".join(clean_path)

        # --- Get dates from frontmatter ---
        published_date = self._parse_date_from_metadata(PUBLISHED_KEYS)
        modified_date = self._parse_date_from_metadata(MODIFIED_KEYS)

        # --- Populate custom_meta ---
        # Exclude standard keys and any keys successfully used for dates
        custom_meta_data = {
            k: v for k, v in self.metadata.items()
            # Check against lowercase reserved keys for case-insensitivity
            if k.lower() not in LOWERCASE_RESERVED_META_KEYS
        }

        # --- Extract prev/next from frontmatter (optional overrides) ---
        prev_page = self.metadata.get('prev')  # Can be None or namespaced URL like 'blog:intro'
        next_page = self.metadata.get('next')  # Can be None or namespaced URL like 'docs:setup'

        # --- Extract sitemap control values ---
        sitemap_priority = self.metadata.get('sitemap_priority')
        if sitemap_priority is not None:
            try:
                sitemap_priority = float(sitemap_priority)
                if not 0.0 <= sitemap_priority <= 1.0:
                    print(f"Warning: sitemap_priority must be 0.0-1.0 in {self.file_path}, got {sitemap_priority}. Ignoring.")
                    sitemap_priority = None
            except (ValueError, TypeError):
                print(f"Warning: Invalid sitemap_priority '{sitemap_priority}' in {self.file_path}. Must be a number 0.0-1.0.")
                sitemap_priority = None

        sitemap_changefreq = self.metadata.get('sitemap_changefreq')
        VALID_CHANGEFREQ = {'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'}
        if sitemap_changefreq and sitemap_changefreq not in VALID_CHANGEFREQ:
            print(f"Warning: Invalid sitemap_changefreq '{sitemap_changefreq}' in {self.file_path}. Valid: {VALID_CHANGEFREQ}. Ignoring.")
            sitemap_changefreq = None

        sitemap_exclude = multi_bool(self.metadata.get('sitemap_exclude', False))

        # --- Create context ---
        return SpellbookContext(
            title=titlefy(remove_leading_dash(
                self.metadata.get('title', self.file_path.stem)) # Keep fallback title
            ),
            # Use the parsed dates, defaults to None if not found/parsed
            published=published_date,
            modified=modified_date,
            url_path=clean_url,
            raw_content=self.raw_content,
            # Use multi_bool for flexibility in is_public
            is_public=multi_bool(self.metadata.get('is_public', True)),
            # Ensure tags is always a list
            tags=self.metadata.get('tags', []) if isinstance(self.metadata.get('tags'), list) else [],
            # Extract author from metadata
            author=self.metadata.get('author'),
            custom_meta=custom_meta_data,
            toc={},  # This will be filled by the command later
            next_page=next_page,  # From frontmatter or None (will be auto-filled by NavigationBuilder)
            prev_page=prev_page,  # From frontmatter or None (will be auto-filled by NavigationBuilder)
            # Sitemap control
            sitemap_priority=sitemap_priority,
            sitemap_changefreq=sitemap_changefreq,
            sitemap_exclude=sitemap_exclude
        )

def multi_bool(value):
    """Allow string false or False or boolean False to be False
    or string true or True or boolean True to be True"""
    if isinstance(value, str):
        # Make comparison case-insensitive and strip whitespace
        val_lower = value.strip().lower()
        if val_lower in ['false', 'f', 'no', 'n', '0']:
            return False
        elif val_lower in ['true', 't', 'yes', 'y', '1']:
            return True
    # Fallback to standard Python boolean conversion for other types (int, bool)
    return bool(value)