# django_spellbook/management/commands/processing/file_writer.py

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

from django.core.management.base import CommandError
from django_spellbook.management.commands.processing.generator_utils import (
    get_spellbook_dir, 
    create_file_if_not_exists, 
    write_file
)

logger = logging.getLogger(__name__)

class FileWriter:
    """
    Handles file I/O operations for the URL and view generators.
    """
    
    INITIAL_URLS_CONTENT = """from django.urls import path
from django_spellbook.{views_module} import *

app_name = '{app_name}'
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

    def __init__(self, content_app: str, url_prefix: str = ''):
        """
        Initialize the file writer.
        
        Args:
            content_app: Django app name where content will be stored
            url_prefix: URL prefix for the content app
        """
        self.content_app = content_app
        self.url_prefix = url_prefix.strip('/')  # Normalize by removing trailing slashes
        self.spellbook_dir = get_spellbook_dir()
        
        # Create module names for app-specific files
        self.urls_module = f"urls_{content_app.replace('-', '_')}"
        self.views_module = f"views_{content_app.replace('-', '_')}"
        
        self._ensure_urls_views_files()
        self._update_main_urls_file()
    
    def _ensure_urls_views_files(self) -> None:
        """Ensure app-specific URLs and views files exist in django_spellbook."""
        # Create app-specific URLs file with proper imports
        urls_content = self.INITIAL_URLS_CONTENT.format(
            views_module=self.views_module,
            app_name=self.content_app
        )
        urls_path = os.path.join(self.spellbook_dir, f"{self.urls_module}.py")
        create_file_if_not_exists(urls_path, urls_content)
        
        # Create app-specific views file with app-specific TOC
        views_content = self.INITIAL_VIEWS_CONTENT.format(app_name=self.content_app)
        views_path = os.path.join(self.spellbook_dir, f"{self.views_module}.py")
        create_file_if_not_exists(views_path, views_content)

        # Create main urls.py file if it doesn't exist
        main_urls_path = os.path.join(self.spellbook_dir, 'urls.py')
        main_urls_content = self.MAIN_URLS_TEMPLATE.format(includes="")
        create_file_if_not_exists(main_urls_path, main_urls_content)
    
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
        # Use the provided URL prefix, even if it's empty
        if self.urls_module not in includes:
            includes[self.urls_module] = self.url_prefix
        slash = '/' if self.url_prefix else ''
        # Generate the includes list for the urlpatterns
        includes_str = ',\n    '.join([
            f"path('{prefix}{slash}', include('django_spellbook.{module}'))" 
            for module, prefix in includes.items()
        ])
        
        # Write the updated main urls.py
        main_urls_content = self.MAIN_URLS_TEMPLATE.format(includes=includes_str)
        write_file(main_urls_path, main_urls_content)

    def write_urls_file(self, url_patterns: List[str]) -> None:
        """Write URL patterns to app-specific urls.py file."""
        try:
            if url_patterns:
                urls_str = ',\n    '.join(url_patterns)
                # Add trailing comma (Python best practice)
                urls_str += ','
            else:
                urls_str = ''

            content = f"""from django.urls import path
from django_spellbook import {self.views_module} as views

app_name = '{self.content_app}'

urlpatterns = [
    {urls_str}
]"""
            file_path = os.path.join(self.spellbook_dir, f"{self.urls_module}.py")
            write_file(file_path, content)
        except Exception as e:
            raise CommandError(f"Failed to write URLs file: {str(e)}")

    def write_views_file(self, view_functions: List[str], toc: Dict) -> None:
        """Write view functions to app-specific views.py file."""
        try:
            views_str = '\n'.join(view_functions) if view_functions else ''
            content = f"""import datetime
from django.shortcuts import render

# Table of Contents for {self.content_app}
TOC = {toc}

{views_str}"""
            file_path = os.path.join(self.spellbook_dir, f"{self.views_module}.py")
            write_file(file_path, content)
        except Exception as e:
            raise CommandError(f"Failed to write views file: {str(e)}")