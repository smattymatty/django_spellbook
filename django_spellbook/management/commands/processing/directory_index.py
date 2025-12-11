# django_spellbook/management/commands/processing/directory_index.py

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.generator_utils import get_clean_url

logger = logging.getLogger(__name__)


class DirectoryIndexBuilder:
    """
    Builds directory index views from processed markdown files.

    Generates view functions and URL patterns for directory listing pages
    that show subdirectories and pages within each directory.
    """

    def __init__(self, content_app: str, url_prefix: str = ''):
        """
        Initialize DirectoryIndexBuilder.

        Args:
            content_app: Django app name where content is stored
            url_prefix: URL prefix for the content app (e.g., 'docs', 'blog')
        """
        self.content_app = content_app
        self.url_prefix = url_prefix.strip('/')

    def build_indexes(
        self,
        processed_files: List[ProcessedFile]
    ) -> Tuple[List[str], List[str]]:
        """
        Build directory index views and URLs for all directories.

        Args:
            processed_files: List of processed markdown files

        Returns:
            Tuple of (view_function_strings, url_pattern_strings)
        """
        if not processed_files:
            logger.debug("No processed files to build directory indexes from")
            return [], []

        # Group files by directory
        directory_groups = self._group_by_directory(processed_files)

        view_functions = []
        url_patterns = []

        for directory, files in directory_groups.items():
            # Skip if directory has URL conflict with existing file
            if self._has_index_conflict(directory, files):
                logger.debug(f"Skipping index for {directory} - URL conflict with existing file")
                continue

            # Skip empty directories (shouldn't happen, but safety check)
            if not files:
                logger.debug(f"Skipping index for {directory} - no files")
                continue

            # Collect directory context
            context_data = self._collect_directory_context(
                directory, files, processed_files
            )

            # Generate view function and URL pattern
            view_func = self._generate_view_function(directory, context_data)
            url_pattern = self._generate_url_pattern(directory)

            view_functions.append(view_func)
            url_patterns.append(url_pattern)

            logger.debug(f"Generated index for {directory} with {len(context_data['pages'])} pages and {len(context_data['subdirectories'])} subdirectories")

        logger.info(f"Generated {len(view_functions)} directory index views")
        return view_functions, url_patterns

    def _group_by_directory(
        self,
        processed_files: List[ProcessedFile]
    ) -> Dict[Path, List[ProcessedFile]]:
        """
        Group processed files by their parent directory.

        Args:
            processed_files: List of processed markdown files

        Returns:
            Dictionary mapping directory path to list of files in that directory
        """
        groups = defaultdict(list)

        for pf in processed_files:
            # Use relative_url to determine directory structure
            # This ensures we work with content-relative paths, not absolute filesystem paths
            relative_url = pf.relative_url.strip('/')

            if '/' in relative_url:
                # File is in a subdirectory - get parent directory from URL
                parent_dir = Path('/'.join(relative_url.split('/')[:-1]))
            else:
                # File is at root
                parent_dir = Path('.')

            groups[parent_dir].append(pf)

        return groups

    def _has_index_conflict(
        self,
        directory: Path,
        files: List[ProcessedFile]
    ) -> bool:
        """
        Check if any file would claim the directory's root URL.

        For example, if directory is /docs and a file generates /docs/ URL,
        we shouldn't generate an automatic index.

        Args:
            directory: Directory path
            files: Files in that directory

        Returns:
            True if conflict exists, False if safe to generate index
        """
        # Build expected directory URL
        dir_url = self._build_directory_url(directory).rstrip('/')

        # Check if any file claims this exact URL
        for pf in files:
            # Build the full URL for this file
            file_url = self._build_page_url(pf.relative_url).rstrip('/')

            if file_url == dir_url:
                # File claims the directory URL (likely index.md or similar)
                return True

        return False

    def _build_directory_url(self, directory: Path) -> str:
        """
        Build URL path for a directory.

        Args:
            directory: Directory path

        Returns:
            URL string (e.g., 'guides/' for subdirs, '' for root)

        Note:
            Does NOT include url_prefix because the Django URLs are included
            at the prefix level (e.g., path('content/', include('urls_cornerstone')))
        """
        # Convert Path to relative URL parts
        parts = []

        # Add directory parts (relative to source root)
        if directory != Path('.'):
            parts.extend(directory.parts)

            # Remove url_prefix if it's the first part (avoid duplication)
            if self.url_prefix and parts and parts[0] == self.url_prefix:
                parts = parts[1:]

        # Build URL with trailing slash (no leading slash for Django path())
        if parts:
            url = '/'.join(parts) + '/'
        else:
            # Root directory = empty string (will be at the include prefix)
            url = ''

        return url

    def _collect_directory_context(
        self,
        directory: Path,
        files: List[ProcessedFile],
        all_files: List[ProcessedFile]
    ) -> dict:
        """
        Build template context for a directory index.

        Args:
            directory: Directory to build context for
            files: Files in this directory
            all_files: All processed files (for subdirectory detection)

        Returns:
            Dictionary with directory_name, directory_path, subdirectories, pages
        """
        # Get directory metadata
        directory_name = self._humanize_directory_name(directory)
        directory_path = self._build_directory_url(directory)

        # Detect subdirectories
        subdirectories = self._detect_subdirectories(directory, all_files)

        # Collect page metadata
        pages = self._collect_page_metadata(files)

        return {
            'directory_name': directory_name,
            'directory_path': directory_path,
            'subdirectories': subdirectories,
            'pages': pages
        }

    def _detect_subdirectories(
        self,
        parent_dir: Path,
        all_files: List[ProcessedFile]
    ) -> List[dict]:
        """
        Find immediate child directories of parent_dir.

        Args:
            parent_dir: Parent directory
            all_files: All processed files

        Returns:
            List of subdirectory dicts with title, url, page_count
        """
        subdirs = defaultdict(int)

        for pf in all_files:
            # Use relative_url to determine file directory
            relative_url = pf.relative_url.strip('/')

            if '/' in relative_url:
                # File is in a subdirectory
                file_dir = Path('/'.join(relative_url.split('/')[:-1]))
            else:
                # File is at root
                file_dir = Path('.')

            # Check if this file is in a subdirectory of parent_dir
            try:
                # Get relative path from parent_dir to file_dir
                relative = file_dir.relative_to(parent_dir)

                # Get immediate child directory (first part of relative path)
                if relative.parts:
                    immediate_child = relative.parts[0]
                    subdirs[immediate_child] += 1

            except ValueError:
                # file_dir is not relative to parent_dir, skip
                continue

        # Build subdirectory list
        subdir_list = []
        for subdir_name, page_count in sorted(subdirs.items()):
            subdir_path = parent_dir / subdir_name
            subdir_url = self._build_directory_url(subdir_path)

            subdir_list.append({
                'title': self._humanize_directory_name(Path(subdir_name)),
                'url': subdir_url,
                'page_count': page_count
            })

        return subdir_list

    def _collect_page_metadata(self, files: List[ProcessedFile]) -> List[dict]:
        """
        Collect metadata for pages in a directory.

        Args:
            files: Files in the directory

        Returns:
            List of page dicts with title, url, published, modified, tags, description
        """
        pages = []

        for pf in files:
            # Build page URL with url_prefix
            page_url = self._build_page_url(pf.relative_url)

            # Get title (fallback to filename)
            # Handle both Path objects and strings for original_path
            original_path = pf.original_path if isinstance(pf.original_path, Path) else Path(pf.original_path)
            title = getattr(pf.context, 'title', None) or original_path.stem.replace('_', ' ').replace('-', ' ').title()

            # Collect metadata
            # Use getattr with default to handle mock objects gracefully
            published = getattr(pf.context, 'published', None)
            modified = getattr(pf.context, 'modified', None)
            tags = getattr(pf.context, 'tags', None) or []
            description = getattr(pf.context, 'description', None)

            page_data = {
                'title': title,
                'url': page_url,
                'published': published,  # Keep as datetime for template's |date filter
                'modified': modified,    # Keep as datetime for template's |date filter
                'tags': tags,
                'description': description
            }

            pages.append(page_data)

        # Sort alphabetically by title
        pages.sort(key=lambda p: p['title'].lower())

        return pages

    def _build_page_url(self, relative_url: str) -> str:
        """
        Build URL for a page (relative, no prefix).

        Args:
            relative_url: Relative URL from ProcessedFile

        Returns:
            URL string without prefix (will be added by include())

        Note:
            Does NOT include url_prefix because the Django URLs are included
            at the prefix level (e.g., path('content/', include('urls_cornerstone')))
        """
        clean_url = get_clean_url(relative_url)

        # Remove url_prefix if it's at the start of the URL
        if self.url_prefix and clean_url.startswith(self.url_prefix + '/'):
            clean_url = clean_url[len(self.url_prefix) + 1:]
        elif self.url_prefix and clean_url == self.url_prefix:
            clean_url = ''

        # Return with trailing slash, no leading slash (for Django path())
        if clean_url:
            return f'{clean_url}/'
        else:
            return ''

    def _humanize_directory_name(self, directory: Path) -> str:
        """
        Convert directory path to human-readable title.

        Args:
            directory: Directory path

        Returns:
            Human-readable string
        """
        if directory == Path('.'):
            return self.content_app.replace('_', ' ').title()

        # Get last part of path (directory name)
        name = directory.name

        # Replace separators with spaces and title case
        name = name.replace('_', ' ').replace('-', ' ')

        # Handle acronyms (API, FAQ, etc.)
        words = name.split()
        title_words = []
        for word in words:
            if word.upper() in ['API', 'FAQ', 'TOC', 'URL', 'HTML', 'CSS', 'JS']:
                title_words.append(word.upper())
            else:
                title_words.append(word.capitalize())

        return ' '.join(title_words)

    def _generate_view_function(
        self,
        directory_path: Path,
        context_data: dict
    ) -> str:
        """
        Generate Python code string for a directory index view function.

        Args:
            directory_path: Directory path
            context_data: Template context dictionary

        Returns:
            View function code as string
        """
        # Generate view name from directory path
        view_name = self._generate_view_name(directory_path)

        # Convert context_data to Python literal string
        context_repr = self._dict_to_python_literal(context_data)

        # Generate view function code
        view_code = f'''
def {view_name}(request):
    """Auto-generated directory index view for {context_data['directory_path']}"""
    context = {context_repr}
    return render(request, 'django_spellbook/directory_index/default.html', context)
'''

        return view_code

    def _generate_url_pattern(self, directory_path: Path) -> str:
        """
        Generate Django URL pattern string for a directory index.

        Args:
            directory_path: Directory path

        Returns:
            URL pattern code as string
        """
        view_name = self._generate_view_name(directory_path)
        directory_url = self._build_directory_url(directory_path)

        # Remove leading slash for Django path()
        url_path = directory_url.lstrip('/')

        # Generate URL name
        url_name = f"{self.content_app}_directory_index_{view_name}"

        return f"path('{url_path}', views.{view_name}, name='{url_name}')"

    def _generate_view_name(self, directory_path: Path) -> str:
        """
        Generate a valid Python function name from directory path.

        Args:
            directory_path: Directory path

        Returns:
            Valid Python identifier
        """
        if directory_path == Path('.'):
            return f'directory_index_root_{self.content_app}'

        # Convert path to valid identifier
        parts = []
        for part in directory_path.parts:
            # Replace invalid characters
            clean = part.replace('-', '_').replace(' ', '_').replace('/', '_')
            # Remove leading/trailing underscores
            clean = clean.strip('_')
            if clean:  # Only add non-empty parts
                parts.append(clean)

        name = '_'.join(parts)
        return f'directory_index_{name}'

    def _dict_to_python_literal(self, d: dict, indent: int = 1) -> str:
        """
        Convert dictionary to Python literal string representation.

        Args:
            d: Dictionary to convert
            indent: Current indentation level

        Returns:
            String representation of dictionary
        """
        if not d:
            return '{}'

        indent_str = '    ' * indent
        lines = ['{']

        for key, value in d.items():
            # Format key
            key_repr = repr(key)

            # Format value
            if isinstance(value, dict):
                value_repr = self._dict_to_python_literal(value, indent + 1)
            elif isinstance(value, list):
                value_repr = self._list_to_python_literal(value, indent + 1)
            elif isinstance(value, str):
                value_repr = repr(value)
            elif value is None:
                value_repr = 'None'
            else:
                value_repr = repr(value)

            lines.append(f'{indent_str}{key_repr}: {value_repr},')

        lines.append('    ' * (indent - 1) + '}')
        return '\n'.join(lines)

    def _list_to_python_literal(self, lst: list, indent: int = 1) -> str:
        """
        Convert list to Python literal string representation.

        Args:
            lst: List to convert
            indent: Current indentation level

        Returns:
            String representation of list
        """
        if not lst:
            return '[]'

        indent_str = '    ' * indent
        lines = ['[']

        for item in lst:
            if isinstance(item, dict):
                item_repr = self._dict_to_python_literal(item, indent + 1)
            elif isinstance(item, list):
                item_repr = self._list_to_python_literal(item, indent + 1)
            elif isinstance(item, str):
                item_repr = repr(item)
            elif item is None:
                item_repr = 'None'
            else:
                item_repr = repr(item)

            lines.append(f'{indent_str}{item_repr},')

        lines.append('    ' * (indent - 1) + ']')
        return '\n'.join(lines)
