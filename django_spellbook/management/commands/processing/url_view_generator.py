# django_spellbook/management/commands/processing/url_view_generator.py

import os
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Optional

from django.core.management.base import CommandError
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.management.commands.processing.file_processor import ProcessedFile

from django_spellbook.utils import remove_leading_dash, get_clean_url

logger = logging.getLogger(__name__)


class URLViewGenerator:
    """
    Handles URL and view generation for markdown-generated content.
    Responsible for creating Django URL patterns and view functions.
    """

    INITIAL_URLS_CONTENT = """from django.urls import path
from django_spellbook.{views_module} import *

urlpatterns = []
"""

    INITIAL_VIEWS_CONTENT = """import datetime
from django.shortcuts import render

# Table of Contents for {app_name}
TOC = {{}}
"""

    MAIN_URLS_TEMPLATE = """from django.urls import path, include

urlpatterns = [
    {includes}
]
"""

    def __init__(self, content_app: str, content_dir_path: str, source_path: str=None):
        """
        Initialize URL and view generator.

        Args:
            content_app (str): Django app name where content will be stored
            content_dir_path (str): Base directory path for content
            source_path (str): Base directory path for source files
        """
        self.source_path = source_path
        self.content_app = content_app
        self.content_dir_path = content_dir_path
        self.spellbook_dir = self._get_spellbook_dir()
        
        # Create app-specific module names
        self.urls_module = f"urls_{content_app.replace('-', '_')}"
        self.views_module = f"views_{content_app.replace('-', '_')}"
        
        self._ensure_urls_views_files()
        self._update_main_urls_file()

    def _get_spellbook_dir(self) -> str:
        """Get the django_spellbook base directory."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

    def _ensure_urls_views_files(self) -> None:
        """Ensure app-specific URLs and views files exist in django_spellbook."""
        # Create app-specific URLs file with proper imports
        urls_content = self.INITIAL_URLS_CONTENT.format(views_module=self.views_module)
        self._create_file_if_not_exists(f"{self.urls_module}.py", urls_content)
        
        # Create app-specific views file with app-specific TOC
        views_content = self.INITIAL_VIEWS_CONTENT.format(app_name=self.content_app)
        self._create_file_if_not_exists(f"{self.views_module}.py", views_content)

        # Create main urls.py file if it doesn't exist
        main_urls_content = self.MAIN_URLS_TEMPLATE.format(includes="")
        self._create_file_if_not_exists('urls.py', main_urls_content)
        
    def _update_main_urls_file(self) -> None:
        """Update main urls.py to include app-specific URL modules."""
        main_urls_path = os.path.join(self.spellbook_dir, 'urls.py')
        
        # Dictionary of existing includes
        includes = {}
        
        if os.path.exists(main_urls_path):
            # Read existing file content
            try:
                with open(main_urls_path, 'r') as f:
                    content = f.read()
                
                # Extract existing includes using regex
                import re
                pattern = r"path\('([^']+)',\s*include\('django_spellbook\.([^']+)'\)\)"
                matches = re.findall(pattern, content)
                
                for prefix, module in matches:
                    # Strip trailing slashes from the prefix
                    cleaned_prefix = prefix.rstrip('/')
                    includes[module] = cleaned_prefix
            except Exception as e:
                logger.error(f"Error reading urls.py: {str(e)}")
        
        # Add current module's include if not already present
        if self.urls_module not in includes:
            includes[self.urls_module] = self.content_app
            
        # Generate the includes list for the urlpatterns
        includes_str = ',\n    '.join([
            f"path('{prefix}/', include('django_spellbook.{module}'))" 
            for module, prefix in includes.items()
        ])
        
        # Write the updated main urls.py
        main_urls_content = self.MAIN_URLS_TEMPLATE.format(includes=includes_str)
        with open(main_urls_path, 'w') as f:
            f.write(main_urls_content)

    def _create_file_if_not_exists(self, filename: str, content: str) -> None:
        """Create a file with initial content if it doesn't exist."""
        file_path = os.path.join(self.spellbook_dir, filename)
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.debug(f"Created new file: {file_path}")
            except IOError as e:
                raise CommandError(f"Failed to create {filename}: {str(e)}")

    def generate_urls_and_views(self, processed_files: List[ProcessedFile], toc: Dict) -> None:
        """
        Generate URL patterns and view functions for processed files.

        Args:
            processed_files: List of processed markdown files
            toc: Table of contents dictionary
        """
        try:
            urls = []
            views = []

            for processed_file in processed_files:
                url_data = self._generate_url_data(processed_file)
                urls.append(url_data['url_pattern'])
                views.append(url_data['view_content'])

            self._write_urls(urls)
            self._write_views(views, toc)
        except Exception as e:
            raise CommandError(f"Failed to generate URLs and views: {str(e)}")

    def _generate_url_data(self, processed_file: ProcessedFile) -> Dict[str, str]:
        """Generate URL pattern and view function for a single file."""
        view_name = self._generate_view_name(
            remove_leading_dash(processed_file.relative_url))
        template_path = self._get_template_path(processed_file.relative_url)
        clean_url = get_clean_url(processed_file.relative_url)
        
        # Create a more user-friendly URL name (just use the last segment)
        path_parts = clean_url.split('/')
        # Create a URL name using the full path
        url_name = clean_url.replace('/', '_')
        
        # Build comprehensive metadata including namespace information
        metadata = {
            'title': getattr(processed_file.context, 'title', path_parts[-1].replace('-', ' ').title()),
            'created_at': getattr(processed_file.context, 'created_at', None),
            'updated_at': getattr(processed_file.context, 'updated_at', None),
            'url_path': clean_url,
            'raw_content': getattr(processed_file.context, 'raw_content', ''),
            'is_public': getattr(processed_file.context, 'is_public', True),
            'tags': getattr(processed_file.context, 'tags', []),
            'custom_meta': getattr(processed_file.context, 'custom_meta', {}),
            'namespace': self.content_app,  # Add app namespace
            'url_name': url_name,  # Simple URL name
            'namespaced_url': f"{self.content_app}:{url_name}"  # Full namespaced URL
        }
        
        return {
            'url_pattern': f"path('{clean_url}/', {view_name}, name='{url_name}')",
            'view_content': self._generate_view_function(
                view_name, 
                template_path, 
                processed_file.context,
                processed_file.relative_url,
                metadata
            )
        }

    def _generate_view_name(self, url_pattern: str) -> str:
        """Generate a valid Python function name from URL pattern."""
        # No need to include 'view_' prefix as it's app-specific now
        return f"{url_pattern.replace('/', '_').replace('.', '_').replace('-', '_')}"

    def _get_template_path(self, relative_url: str) -> str:
        """Generate template path from relative URL."""
        return os.path.join(self.content_app, 'spellbook_md', relative_url + '.html')

    def _generate_view_function(self, view_name: str, template_path: str, 
                            context: SpellbookContext, relative_url: str, 
                            metadata: Dict) -> str:
        """Generate Django view function content."""
        context_dict = self._prepare_context_dict(context)
        clean_url = get_clean_url(relative_url)
        
        # Convert metadata to string representation for inclusion in the view
        metadata_repr = "{\n"
        for k, v in metadata.items():
            metadata_repr += f"        '{k}': {repr(v)},\n"
        metadata_repr += "    }"
        
        return f"""
def {view_name}(request):
    context = {context_dict}
    context['toc'] = TOC 
    context['current_url'] = '{clean_url}'
    context['metadata'] = {metadata_repr}
    return render(request, '{template_path}', context)
"""

    def _prepare_context_dict(self, context: SpellbookContext) -> Dict:
        """Prepare context dictionary for template rendering."""
        context_dict = context.__dict__.copy()
        if 'toc' in context_dict:
            del context_dict['toc']  # Remove the existing toc

        return {
            k: repr(v) if isinstance(
                v, (datetime.datetime, datetime.date)) else v
            for k, v in context_dict.items()
        }

    def _write_urls(self, urls: List[str]) -> None:
        """Write URL patterns to app-specific urls.py file."""
        try:
            # Process URLs as before
            processed_urls = []
            for url in urls:
                prefix, url_path, suffix = url.split("'", 2)
                split_path = url_path.split('/')
                clean_split_path = []
                for part in split_path:
                    clean_split_path.append(remove_leading_dash(part))
                clean_path = "/".join(clean_split_path)
                processed_urls.append(f"{prefix}'{clean_path}'{suffix}")

            content = self._generate_urls_file_content(processed_urls)
            self._write_file(f'{self.urls_module}.py', content)
        except Exception as e:
            raise CommandError(f"Failed to write URLs file: {str(e)}")

    def _generate_urls_file_content(self, urls: List[str]) -> str:
        """Generate content for app-specific urls.py file."""
        urls_str = ',\n    '.join(urls) if urls else ''
        return """from django.urls import path
        
app_name = '{}'
from django_spellbook.{} import *

urlpatterns = [
    {}
]""".format(self.content_app, self.views_module, urls_str)

    def _write_views(self, views: List[str], toc: Dict) -> None:
        """Write view functions to app-specific views.py file."""
        try:
            content = self._generate_views_file_content(views, toc)
            self._write_file(f'{self.views_module}.py', content)
        except Exception as e:
            raise CommandError(f"Failed to write views file: {str(e)}")

    def _generate_views_file_content(self, views: List[str], toc: Dict) -> str:
        """Generate content for app-specific views.py file."""
        views_str = '\n'.join(views) if views else ''
        return """import datetime
from django.shortcuts import render

# Table of Contents for {}
TOC = {}

{}""".format(self.content_app, toc, views_str)

    def _write_file(self, filename: str, content: str) -> None:
        """Write content to a file in the spellbook directory."""
        file_path = os.path.join(self.spellbook_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except IOError as e:
            raise CommandError(f"Failed to write {filename}: {str(e)}")