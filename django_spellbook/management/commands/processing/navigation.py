# django_spellbook/management/commands/processing/navigation.py

import logging
from typing import List, Dict, Tuple
from pathlib import Path
from collections import defaultdict

from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.generator_utils import get_clean_url

logger = logging.getLogger(__name__)


class NavigationBuilder:
    """
    Builds prev/next navigation links for processed markdown files.

    Navigation rules:
    1. Files are grouped by content_app AND parent directory
    2. Within each group, files are sorted alphabetically
    3. Frontmatter overrides (prev/next in YAML) take precedence
    4. Navigation respects app and directory boundaries
    """

    @staticmethod
    def build_navigation(processed_files: List[ProcessedFile], content_app: str) -> None:
        """
        Build navigation links for all processed files.

        Mutates ProcessedFile.context objects in-place to set prev_page and next_page.

        Args:
            processed_files: List of processed markdown files
            content_app: Name of the content app (used for namespaced URLs)
        """
        if not processed_files:
            logger.debug("No processed files to build navigation for")
            return

        # Group files by parent directory
        groups = NavigationBuilder._group_files(processed_files)

        # Build navigation for each group independently
        for directory, files in groups.items():
            logger.debug(f"Building navigation for {len(files)} files in {content_app}:{directory}")
            NavigationBuilder._build_group_navigation(files, content_app, processed_files)

    @staticmethod
    def _group_files(processed_files: List[ProcessedFile]) -> Dict[str, List[ProcessedFile]]:
        """
        Group files by parent directory.

        Args:
            processed_files: List of processed markdown files

        Returns:
            Dictionary mapping directory to list of files
        """
        groups = defaultdict(list)

        for pf in processed_files:
            # Get parent directory from original path
            parent_dir = Path(pf.original_path).parent

            # Group by directory
            groups[str(parent_dir)].append(pf)

        return groups

    @staticmethod
    def _build_group_navigation(files: List[ProcessedFile], app: str, all_files: List[ProcessedFile]) -> None:
        """
        Build navigation for a group of files in the same app/directory.

        Args:
            files: List of files in the same app and directory
            app: Content app name
            all_files: All processed files (for path-based navigation lookup)
        """
        # Sort files alphabetically
        sorted_files = sorted(files, key=NavigationBuilder._get_sort_key)

        # Build navigation chain
        for i, current_file in enumerate(sorted_files):
            # Check if frontmatter already specifies prev/next
            fm_prev = NavigationBuilder._get_frontmatter_override(current_file, 'prev')
            fm_next = NavigationBuilder._get_frontmatter_override(current_file, 'next')

            # Set prev_page (use frontmatter override if available)
            if fm_prev is not None:
                # Normalize frontmatter value (supports both path and namespaced formats)
                current_file.context.prev_page = NavigationBuilder._normalize_navigation_value(
                    fm_prev, all_files, app
                )
                logger.debug(f"Using frontmatter prev for {current_file.relative_url}: {current_file.context.prev_page}")
            elif i > 0:
                prev_file = sorted_files[i - 1]
                current_file.context.prev_page = NavigationBuilder._build_namespaced_url(prev_file, app)
                logger.debug(f"Auto prev for {current_file.relative_url}: {current_file.context.prev_page}")
            else:
                # First file in group, no previous
                current_file.context.prev_page = None

            # Set next_page (use frontmatter override if available)
            if fm_next is not None:
                # Normalize frontmatter value (supports both path and namespaced formats)
                current_file.context.next_page = NavigationBuilder._normalize_navigation_value(
                    fm_next, all_files, app
                )
                logger.debug(f"Using frontmatter next for {current_file.relative_url}: {current_file.context.next_page}")
            elif i < len(sorted_files) - 1:
                next_file = sorted_files[i + 1]
                current_file.context.next_page = NavigationBuilder._build_namespaced_url(next_file, app)
                logger.debug(f"Auto next for {current_file.relative_url}: {current_file.context.next_page}")
            else:
                # Last file in group, no next
                current_file.context.next_page = None

    @staticmethod
    def _get_sort_key(processed_file: ProcessedFile) -> str:
        """
        Generate sort key for a file.

        Args:
            processed_file: Processed markdown file

        Returns:
            String key for sorting (lowercase filename)
        """
        filename = Path(processed_file.original_path).name.lower()
        return filename

    @staticmethod
    def _get_frontmatter_override(processed_file: ProcessedFile, field: str) -> str:
        """
        Get frontmatter override for prev or next field.

        Args:
            processed_file: Processed markdown file
            field: 'prev' or 'next'

        Returns:
            Frontmatter value if present, None otherwise
        """
        # The frontmatter parser should have already extracted prev/next
        # and stored them in the context
        result = processed_file.context.get_safe_attr(field + '_page', None)

        # Ensure result is a string or None (not a Mock or other type)
        if result is not None and not isinstance(result, str):
            logger.debug(f"Frontmatter override for {field} is not a string: {type(result).__name__}, treating as None")
            return None

        return result

    @staticmethod
    def _is_namespaced_format(value: str) -> bool:
        """
        Check if value is in namespaced format (app:page) vs path format (path/to/page).

        Namespaced format: "app_name:url_name"
        - Has exactly one ':'
        - Part before ':' contains no '/'
        - Examples: "blog:page", "docs:---intro", "my_app:sub_page"

        Path format: "path/to/page" or "page"
        - No ':' OR ':' appears after '/'
        - Examples: "intro", "guides/setup"

        Args:
            value: Navigation value from frontmatter

        Returns:
            True if namespaced format, False if path format
        """
        # Ensure value is a string
        if not isinstance(value, str):
            return False

        if ':' not in value:
            return False  # No colon = path format

        # Split on first colon
        parts = value.split(':', 1)
        if len(parts) != 2:
            return False

        app_part = parts[0]

        # If app part contains '/', it's probably a path (invalid but treat as path)
        if '/' in app_part:
            return False

        # If app part is empty, it's invalid (":something") - treat as path
        if not app_part:
            return False

        # Looks like valid namespaced format: "app:page"
        return True

    @staticmethod
    def _normalize_navigation_value(value: str, processed_files: List[ProcessedFile], app: str) -> str:
        """
        Convert frontmatter navigation value to namespaced URL format.

        Supports two formats:
        1. Namespaced: "blog:page-name" (use as-is)
        2. Path-based: "path/to/page" or "page" (convert to namespaced)

        Args:
            value: Raw frontmatter value (prev or next)
            processed_files: All processed files (for lookup)
            app: Current content app

        Returns:
            Namespaced URL string
        """
        # Ensure value is a string
        if not isinstance(value, str):
            logger.warning(f"Navigation value is not a string: {type(value).__name__}")
            return ""

        # Already in namespaced format - use as-is
        if NavigationBuilder._is_namespaced_format(value):
            logger.debug(f"Navigation value '{value}' is already namespaced")
            return value

        # Path-based - find matching file and convert
        clean_path = get_clean_url(value)
        logger.debug(f"Converting path-based navigation '{value}' (clean: '{clean_path}')")

        # Search for matching file by relative_url
        for pf in processed_files:
            pf_clean_url = get_clean_url(pf.relative_url)
            if pf_clean_url == clean_path:
                namespaced = NavigationBuilder._build_namespaced_url(pf, app)
                logger.debug(f"Found matching file: '{pf.relative_url}' -> '{namespaced}'")
                return namespaced

        # Fallback: construct namespaced URL from path
        # (in case file isn't in current batch or will be added later)
        url_name = clean_path.replace('/', '_')
        fallback = f"{app}:{url_name}"
        logger.debug(f"No matching file found, using fallback: '{fallback}'")
        return fallback

    @staticmethod
    def _build_namespaced_url(processed_file: ProcessedFile, app: str) -> str:
        """
        Generate namespaced URL for a processed file.

        Format: app_name:url_name (e.g., 'blog:01_intro', 'docs:setup')

        Args:
            processed_file: Processed markdown file
            app: Content app name

        Returns:
            Namespaced URL string
        """
        clean_url = get_clean_url(processed_file.relative_url)
        url_name = clean_url.replace('/', '_')

        return f"{app}:{url_name}"
