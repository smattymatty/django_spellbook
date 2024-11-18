# django_spellbook/management/commands/processing/url_view_generator.py

import os
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Optional

from django.core.management.base import CommandError
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.management.commands.processing.file_processor import ProcessedFile

logger = logging.getLogger(__name__)


class URLViewGenerator:
    """
    Handles URL and view generation for markdown-generated content.
    Responsible for creating Django URL patterns and view functions.
    """

    INITIAL_URLS_CONTENT = """from django.urls import path
from . import views

urlpatterns = []
"""

    INITIAL_VIEWS_CONTENT = """from django.shortcuts import render
"""

    def __init__(self, content_app: str, content_dir_path: str):
        """
        Initialize URL and view generator.

        Args:
            content_app (str): Django app name where content will be stored
            content_dir_path (str): Base directory path for content
        """
        self.content_app = content_app
        self.content_dir_path = content_dir_path
        self.spellbook_dir = self._get_spellbook_dir()
        self._ensure_urls_views_files()

    def _get_spellbook_dir(self) -> str:
        """Get the django_spellbook base directory."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

    def _ensure_urls_views_files(self) -> None:
        """Ensure URLs and views files exist in django_spellbook."""
        required_files = {
            'urls.py': self.INITIAL_URLS_CONTENT,
            'views.py': self.INITIAL_VIEWS_CONTENT
        }

        for filename, initial_content in required_files.items():
            self._create_file_if_not_exists(filename, initial_content)

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
        """
        Generate URL pattern and view function for a single file.

        Args:
            processed_file: Processed markdown file data

        Returns:
            Dictionary containing URL pattern and view function content
        """
        view_name = self._generate_view_name(processed_file.relative_url)
        template_path = self._get_template_path(processed_file.relative_url)

        return {
            'url_pattern': f"path('{processed_file.relative_url}', views.{view_name}, name='{view_name}')",
            'view_content': self._generate_view_function(view_name, template_path, processed_file.context)
        }

    def _generate_view_name(self, url_pattern: str) -> str:
        """Generate a valid Python function name from URL pattern."""
        return f"view_{url_pattern.replace('/', '_').replace('.', '_')}"

    def _get_template_path(self, relative_url: str) -> str:
        """Generate template path from relative URL."""
        return os.path.join(self.content_app, 'spellbook_md', relative_url + '.html')

    def _generate_view_function(self, view_name: str, template_path: str, context: SpellbookContext) -> str:
        """
        Generate Django view function content.

        Args:
            view_name: Name of the view function
            template_path: Path to the template
            context: SpellbookContext instance

        Returns:
            String containing view function definition
        """
        context_dict = self._prepare_context_dict(context)

        return f"""
def {view_name}(request):
    context = {context_dict}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, '{template_path}', context)
"""

    def _prepare_context_dict(self, context: SpellbookContext) -> Dict:
        """
        Prepare context dictionary for template rendering.

        Args:
            context: SpellbookContext instance

        Returns:
            Dictionary with processed context values
        Example: 
            {
                'title': 'My Page',
                'created_at': '2023-01-01 12:00:00',
                'updated_at': '2023-01-01 12:00:00',
                'url_path': 'my/page',
                'raw_content': '# My Page\nThis is my page content',
                'is_public': True,
                'tags': ['tag1', 'tag2'],
                'custom_meta': {'key': 'value'},
                'toc': {...},
                'next_page': 'next/page',
                'prev_page': 'prev/page'
            }
        """
        context_dict = context.__dict__.copy()
        del context_dict['toc']  # Remove the existing toc

        return {
            k: repr(v) if isinstance(
                v, (datetime.datetime, datetime.date)) else v
            for k, v in context_dict.items()
        }

    def _write_urls(self, urls: List[str]) -> None:
        """Write URL patterns to urls.py file."""
        try:
            content = self._generate_urls_file_content(urls)
            self._write_file('urls.py', content)
        except Exception as e:
            raise CommandError(f"Failed to write URLs file: {str(e)}")

    def _generate_urls_file_content(self, urls: List[str]) -> str:
        """Generate content for urls.py file."""
        return """from django.urls import path
from . import views

urlpatterns = [
    {}
]""".format(',\n    '.join(urls))

    def _write_views(self, views: List[str], toc: Dict) -> None:
        """Write view functions to views.py file."""
        try:
            content = self._generate_views_file_content(views, toc)
            self._write_file('views.py', content)
        except Exception as e:
            raise CommandError(f"Failed to write views file: {str(e)}")

    def _generate_views_file_content(self, views: List[str], toc: Dict) -> str:
        """Generate content for views.py file."""
        return """import datetime
from django.shortcuts import render

# Table of Contents for all views
TOC = {toc}

{views}""".format(toc=toc, views='\n'.join(views))

    def _write_file(self, filename: str, content: str) -> None:
        """Write content to a file in the spellbook directory."""
        file_path = os.path.join(self.spellbook_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except IOError as e:
            raise CommandError(f"Failed to write {filename}: {str(e)}")
