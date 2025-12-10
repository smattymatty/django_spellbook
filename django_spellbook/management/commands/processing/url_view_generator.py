# django_spellbook/management/commands/processing/url_view_generator.py

import os
import logging
from typing import List, Dict, Optional

from django.core.management.base import CommandError
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.url_generator import URLGenerator
from django_spellbook.management.commands.processing.view_generator import ViewGenerator
from django_spellbook.management.commands.processing.file_writer import FileWriter
from django_spellbook.management.commands.processing.navigation import NavigationBuilder
from django_spellbook.management.commands.processing.directory_index import DirectoryIndexBuilder

logger = logging.getLogger(__name__)

class URLGenerationError(Exception):
    """Base exception for all URL generation errors."""
    pass

class URLViewGenerator:
    """
    Coordinates URL and view generation for markdown-generated content.
    Acts as a facade for the URLGenerator, ViewGenerator, and FileWriter components.
    """
    
    def __init__(
        self, 
        content_app: str, 
        content_dir_path: str, 
        source_path: str=None,
        url_prefix: str = ''
        ):
        """
        Initialize URL and view generator.

        Args:
            content_app (str): Django app name where content will be stored
            content_dir_path (str): Base directory path for content
            source_path (str): Base directory path for source files
            url_prefix (str): URL prefix for the content app
        """
        self.source_path = source_path
        self.content_app = content_app
        self.content_dir_path = content_dir_path
        self.url_prefix = url_prefix
        
        # Initialize components
        self.url_generator = URLGenerator(content_app)
        self.view_generator = ViewGenerator(content_app, url_prefix)
        self.file_writer = FileWriter(content_app, url_prefix)
    
    def generate_urls_and_views(self, processed_files: List[ProcessedFile], toc: Dict) -> None:
        """
        Generate URL patterns and view functions for processed files.

        Args:
            processed_files: List of processed markdown files
            toc: Table of contents dictionary
        """
        try:
            # Build navigation links BEFORE generating views
            # This mutates the ProcessedFile.context objects to add prev_page and next_page
            logger.info(f"Building navigation for {len(processed_files)} files")
            NavigationBuilder.build_navigation(processed_files, self.content_app)

            # Build directory index views
            logger.info("Generating directory index pages")
            index_builder = DirectoryIndexBuilder(self.content_app, self.url_prefix)
            index_views, index_urls = index_builder.build_indexes(processed_files)

            # Generate URL patterns
            url_patterns = self.url_generator.generate_url_patterns(processed_files)

            # Generate view functions
            view_functions = self.view_generator.generate_view_functions(processed_files)

            # Combine regular + index patterns/views
            all_views = view_functions + index_views
            all_urls = url_patterns + index_urls

            logger.info(f"Generated {len(index_views)} directory index views")
            logger.info(f"Total views: {len(all_views)}, Total URLs: {len(all_urls)}")

            # Write to files
            self.file_writer.write_urls_file(all_urls)
            self.file_writer.write_views_file(all_views, toc)
        except Exception as e:
            raise CommandError(f"Failed to generate URLs and views: {str(e)}")