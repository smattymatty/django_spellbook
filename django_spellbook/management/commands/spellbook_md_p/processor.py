# django_spellbook/management/commands/spellbook_md/processor.py

import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.file_processor import MarkdownFileProcessor, ProcessedFile
from django_spellbook.management.commands.processing.template_generator import TemplateGenerator
from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
from django_spellbook.management.commands.command_utils import get_folder_list
from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.markdown.toc import TOCGenerator

logger = logging.getLogger(__name__)

class MarkdownProcessor:
    """Handles processing of markdown files into HTML templates and URL/view generation."""
    
    def __init__(self, content_app, source_path, content_dir_path, template_dir):
        self.content_app = content_app
        self.source_path = source_path
        self.content_dir_path = content_dir_path
        self.template_dir = template_dir
        
        # Initialize sub-processors
        self.file_processor = MarkdownFileProcessor()
        self.file_processor.current_source_path = source_path
        self.template_generator = TemplateGenerator(content_app, template_dir)
        self.url_generator = URLViewGenerator(
            content_app=content_app,
            content_dir_path=content_dir_path,
            source_path=source_path
        )
    
    def build_toc(self):
        """Build complete table of contents."""
        toc_generator = TOCGenerator()

        for dirpath, dirnames, filenames in os.walk(self.source_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    try:
                        file_path = Path(dirpath) / filename
                        relative_path = file_path.relative_to(Path(self.source_path))
                        url = f"{self.content_app}:" + str(relative_path.with_suffix('')).replace('\\', '/')
                        url = url.replace('/', '_')
                        
                        # Get title from frontmatter
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        frontmatter = FrontMatterParser(content, file_path)
                        title = frontmatter.metadata.get('title', relative_path.stem)

                        toc_generator.add_entry(relative_path, title, url)
                    except Exception as e:
                        logger.error(f"Error adding TOC entry for {filename}: {str(e)}")
                        continue
        
        return toc_generator.get_toc()
    
    def process_file(self, dirpath, filename, complete_toc):
        """Process a single markdown file."""
        try:
            folder_list = get_folder_list(dirpath, self.source_path)
            html_content, file_path, context = self.file_processor.process_file(
                Path(dirpath), dirpath, filename, folder_list
            )
            
            relative_path = Path(file_path).relative_to(Path(self.source_path))
            template_path = self.template_generator.get_template_path(
                filename, folder_list
            )
            relative_url = str(relative_path.with_suffix('')).replace('\\', '/')
            
            # Use the complete TOC for all files
            context.toc = complete_toc
            
            processed_file = ProcessedFile(
                original_path=file_path,
                html_content=html_content,
                template_path=template_path,
                relative_url=relative_url,
                context=context
            )
            
            self.template_generator.create_template(
                template_path,
                html_content
            )
            
            return processed_file
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            return None
    
    def generate_urls_and_views(self, processed_files, complete_toc):
        """Generate URLs and views for processed files."""
        if processed_files:
            self.url_generator.generate_urls_and_views(processed_files, complete_toc)