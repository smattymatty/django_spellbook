# django_spellbook/management/commands/spellbook_md_p/processor.py

import os
import logging
from typing import List, Dict, Tuple, Optional, Any, Union
from pathlib import Path

from django.core.management.base import CommandError

from django_spellbook.management.commands.processing.file_processor import (
    MarkdownFileProcessor, ProcessedFile, MarkdownProcessingError
)
from django_spellbook.management.commands.processing.generator_utils import (
    remove_leading_dash,

)
from django_spellbook.management.commands.processing.template_generator import TemplateGenerator, TemplateError
from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator, URLGenerationError
from django_spellbook.management.commands.command_utils import get_folder_list
from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.markdown.toc import TOCGenerator, TOCEntry

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

logger = logging.getLogger(__name__)

class MarkdownProcessorError(Exception):
    """Base exception for all markdown processor errors."""
    pass

class TOCBuildingError(MarkdownProcessorError):
    """Exception raised when building the table of contents fails."""
    pass

class FileProcessingError(MarkdownProcessorError):
    """Exception raised when processing a markdown file fails."""
    pass

class MarkdownProcessor:
    """
    Handles processing of markdown files into HTML templates and URL/view generation.
    
    This class orchestrates the entire process of converting markdown files to HTML
    templates and generating the necessary URLs and views to make the content accessible.
    
    Attributes:
        content_app (str): Name of the content app
        source_path (Path): Path to the source directory
        content_dir_path (Path): Path to the content app directory
        template_dir (Path): Path to the template directory
        file_processor (MarkdownFileProcessor): Processor for individual markdown files
        template_generator (TemplateGenerator): Generator for HTML templates
        url_generator (URLViewGenerator): Generator for URLs and views
        reporter (MarkdownReporter): Reporter for the command
    
    Args:
        content_app: Name of the content app
        source_path: Path to the source directory
        content_dir_path: Path to the content app directory
        template_dir: Path to the template directory
        base_template: Base template for the content app
    """
    
    def __init__(
        self,
        content_app: str,
        source_path: Union[str, Path],
        content_dir_path: Union[str, Path],
        template_dir: Union[str, Path],
        reporter: MarkdownReporter,
        url_prefix: str = '',
        base_template: Optional[str] = None,
        extend_from: Optional[str] = None,
    ):
        self.content_app: str = content_app
        self.source_path: Path = Path(source_path)
        self.content_dir_path: Path = Path(content_dir_path)
        self.template_dir: Path = Path(template_dir)
        self.url_prefix: str = url_prefix
        self.reporter: MarkdownReporter = reporter

        # Determine final base template
        # Priority: EXTEND_FROM > BASE_TEMPLATE > default
        if extend_from:
            # Import here to avoid circular imports
            from django_spellbook.management.commands.processing.base_template_generator import SpellbookBaseGenerator

            # Generate wrapper and use it
            base_gen = SpellbookBaseGenerator(
                content_app,
                Path(template_dir),
                extend_from
            )
            final_base = base_gen.process()  # Returns '{app}/spellbook_base.html' or None
        elif base_template:
            # Use explicit base template
            final_base = base_template
        else:
            # Use default
            final_base = 'django_spellbook/bases/sidebar_left.html'

        # Initialize sub-processors
        self.file_processor = MarkdownFileProcessor(self.reporter)
        self.file_processor.current_source_path = str(self.source_path)
        self.template_generator = TemplateGenerator(content_app, str(self.template_dir), final_base)
        self.url_generator = URLViewGenerator(
            content_app=content_app,
            content_dir_path=str(self.content_dir_path),
            source_path=str(self.source_path),
            url_prefix=self.url_prefix
        )

        logger.debug(f"Initialized MarkdownProcessor for app {content_app}")
    
    def build_toc(self) -> Dict[str, TOCEntry]:
        """
        Build complete table of contents from all markdown files in the source path.
        
        This method walks through the source directory, extracts metadata from each
        markdown file, and builds a hierarchical table of contents structure.
        
        Returns:
            Dict[str, TOCEntry]: Complete table of contents mapping paths to TOC entries
            
        Raises:
            TOCBuildingError: If there is an error building the table of contents
        """
        toc_generator = TOCGenerator()
        logger.info(f"Building table of contents from {self.source_path}")

        try:
            # First, collect all markdown files to process
            md_files = []
            for dirpath, _, filenames in os.walk(str(self.source_path)):
                for filename in [f for f in filenames if f.endswith('.md')]:
                    file_path = Path(dirpath) / filename
                    md_files.append(file_path)
            
            # Sort files to ensure deterministic order (root files first)
            md_files.sort(key=lambda p: len(p.parts))
            
            # Process each file
            for file_path in md_files:
                try:
                    relative_path = file_path.relative_to(self.source_path)
                    url = f"{self.content_app}:" + remove_leading_dash(str(relative_path.with_suffix('')).replace('\\', '/'))
                    url = url.replace('/', '_')
                    
                    # Get title from frontmatter
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    frontmatter = FrontMatterParser(content, str(file_path))
                    title = frontmatter.metadata.get('title', relative_path.stem)

                    logger.debug(f"Adding TOC entry for {relative_path}: {title}")
                    toc_generator.add_entry(relative_path, title, url)
                except Exception as e:
                    logger.error(f"Error adding TOC entry for {file_path}: {str(e)}")
                    # Continue with next file instead of failing completely
                    continue

            # Add directory URLs to the TOC
            # Collect all unique directories that contain files
            directories = set()
            for file_path in md_files:
                relative_path = file_path.relative_to(self.source_path)
                parent_path = relative_path.parent

                # Add all parent directories in the path
                while parent_path != Path('.'):
                    directories.add(parent_path)
                    parent_path = parent_path.parent

            # Set URL for each directory
            for directory in sorted(directories):
                # Generate URL name for this directory to match DirectoryIndexBuilder format
                # DirectoryIndexBuilder creates view_name, then URL is {app}_directory_index_{view_name}
                parts = []
                for part in directory.parts:
                    # Replace invalid characters (same as DirectoryIndexBuilder)
                    clean = part.replace('-', '_').replace(' ', '_').replace('/', '_')
                    clean = clean.strip('_')
                    if clean:
                        parts.append(clean)

                # Match DirectoryIndexBuilder's _generate_view_name format exactly
                if not parts:  # Root directory - Path('.')
                    view_name = f'directory_index_root_{self.content_app}'
                else:
                    view_name = '_'.join(parts)

                # URL name format: {app}_directory_index_{view_name}
                directory_url = f"{self.content_app}:{self.content_app}_directory_index_{view_name}"

                logger.debug(f"Adding directory URL for {directory}: {directory_url}")
                toc_generator.set_directory_url(directory, directory_url)

            toc = toc_generator.get_toc()
            logger.info(f"Built TOC with {len(toc['children']) if 'children' in toc else 0} entries")
            return toc
                
        except Exception as e:
            error_msg = f"Failed to build table of contents: {str(e)}"
            logger.error(error_msg)
            raise TOCBuildingError(error_msg) from e
    
    def process_file(
        self, 
        dirpath: str, 
        filename: str, 
        complete_toc: Dict[str, TOCEntry]
    ) -> ProcessedFile:
        """
        Process a single markdown file, converting it to HTML and creating a template.
        
        Args:
            dirpath: Path to the directory containing the markdown file
            filename: Name of the markdown file
            complete_toc: Complete table of contents
            
        Returns:
            ProcessedFile: Object containing the processed file information
            
        Raises:
            FileProcessingError: If there is an error processing the file
        """
        logger.info(f"Processing file: {filename}")
        file_path = Path(dirpath) / filename
        
        # Validate inputs
        if not file_path.exists():
            error_msg = f"File does not exist: {file_path}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg)
            
        if not filename.endswith('.md'):
            error_msg = f"Not a markdown file: {filename}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg)
        
        try:
            # Get folder structure for path construction
            folder_list = get_folder_list(dirpath, str(self.source_path))
            
            # Process markdown to HTML
            html_content, processed_path, context = self.file_processor.process_file(
                Path(dirpath), dirpath, filename, folder_list
            )
            
            # Generate relative paths for templates and URLs
            relative_path = Path(processed_path).relative_to(self.source_path)
            template_path = self.template_generator.get_template_path(
                filename, folder_list
            )
            relative_url = str(relative_path.with_suffix('')).replace('\\', '/')
            
            # Add TOC to context
            context.toc = complete_toc
            
            # Create the processed file object
            processed_file = ProcessedFile(
                original_path=str(processed_path),
                html_content=html_content,
                template_path=template_path,
                relative_url=relative_url,
                context=context
            )
            
            # Create the actual template file
            self.template_generator.create_template(
                template_path,
                html_content
            )
            
            logger.debug(f"Successfully processed {filename} to {template_path}")
            return processed_file
            
        except MarkdownProcessingError as e:
            error_msg = f"Error processing markdown file {filename}: {str(e)}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg) from e
        except TemplateError as e:
            error_msg = f"Error creating template for {filename}: {str(e)}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error processing {filename}: {str(e)}"
            logger.error(error_msg)
            raise FileProcessingError(error_msg) from e
    
    def generate_urls_and_views(
        self, 
        processed_files: List[ProcessedFile], 
        complete_toc: Dict[str, TOCEntry]
    ) -> None:
        """
        Generate URLs and views for all processed files.
        
        This method creates the necessary URL patterns and view functions to make
        the processed markdown content accessible via the web.
        
        Args:
            processed_files: List of successfully processed files
            complete_toc: Complete table of contents
            
        Raises:
            MarkdownProcessorError: If there is an error generating URLs and views
        """
        logger.info(f"Generating URLs and views for {len(processed_files)} files")
        
        if not processed_files:
            logger.warning("No processed files to generate URLs and views for")
            return
            
        try:
            self.url_generator.generate_urls_and_views(processed_files, complete_toc)
            logger.info(f"Successfully generated URLs and views for {len(processed_files)} files")
        except URLGenerationError as e:
            error_msg = f"Error generating URLs and views: {str(e)}"
            logger.error(error_msg)
            raise MarkdownProcessorError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error generating URLs and views: {str(e)}"
            logger.error(error_msg)
            raise MarkdownProcessorError(error_msg) from e