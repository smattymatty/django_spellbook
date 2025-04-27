# django_spellbook/management/commands/spellbook_md.py
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django_spellbook.management.commands.command_utils import (
    validate_spellbook_settings,
    setup_directory_structure
)
from django_spellbook.management.commands.spellbook_md_p.discovery import (
    discover_blocks,
    find_markdown_files
)
from django_spellbook.management.commands.spellbook_md_p.processor import (
    MarkdownProcessor
)

from django_spellbook.management.commands.spellbook_md_p.reporter import (
    MarkdownReporter
)
from django_spellbook.management.commands.spellbook_md_p.exceptions import *

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Converts markdown to html, with a spellbook twist"

    def add_arguments(self, parser):
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue processing files even if some fail'
        )
        parser.add_argument(
            '--report-level',
            choices=['minimal', 'detailed', 'debug'],
            default='detailed',
            help='Level of detail in the report (minimal, detailed, or debug)'
        )
        parser.add_argument(
            '--report-format',
            choices=['text', 'json', 'none'],
            default='text',
            help='Format of the report (text, json, or none to suppress)'
        )
        parser.add_argument(
            '--report-output',
            type=str,
            help='File path to save the report (default: print to stdout)'
        )

    def handle(self, *args, **options):
        """Process markdown files from all configured source-destination pairs."""
        self.continue_on_error = options.get('continue_on_error', False)
        
        # Extract Reporting Options
        self.report_level = options.get('report_level', 'detailed')
        self.report_format = options.get('report_format', 'text')
        self.report_output = options.get('report_output', None)
        
        self.reporter = MarkdownReporter(
            self.stdout,
            self.style,
            report_level=self.report_level,
            report_format=self.report_format,
            report_output=self.report_output
            )
        try:
            self.discover_spellblocks()
            # Validate settings (Should all be List[str] of equal lengths)
            md_file_paths, content_apps, md_url_prefix, base_templates = self.validate_settings()
            print(f"Base templates: {base_templates}")
            # Process each source-destination pair
            pair_results: List[Tuple[str, str, bool, int]] = self.process_each_source_pair(md_file_paths, content_apps, md_url_prefix, base_templates)
            # (md_path, content_app, success, processed_count)
            # Output Summary Report
            self.summary_report(pair_results)
                
        except Exception as e:
            error_message = f"Command failed: {str(e)}"
            self.reporter.error(error_message)
            logger.error(f"Command failed: {str(e)}", exc_info=True)
            raise

    def _process_source_destination_pair(self, md_path: Path, content_app: str, md_url_prefix: str, base_template: str):
        """
        Process all markdown files for a single source-destination pair.
        
        Args:
            md_path (Path): Path to the source markdown directory
            content_app (str): Name of the content app
            md_url_prefix (str): URL prefix for the content app
            base_template (str): Base template for the content app
            
        Raises:
            ContentDiscoveryError if no markdown files are found
            
        Returns:
            Length of the processed files list
        """
        # Find markdown files
        try:
            markdown_files = find_markdown_files(md_path)
            
            if not markdown_files:
                error_message = f"No markdown files found in {md_path}"
                self.reporter.error(error_message)
                self.reporter.write(
                    f"Make sure the directory exists and contains .md files."
                )
                raise ContentDiscoveryError(error_message)
                
            self.reporter.write(f"Found {len(markdown_files)} markdown files to process")
            
        except ContentDiscoveryError:
            raise
        except Exception as e:
            logger.error(f"Error discovering markdown files: {str(e)}", exc_info=True)
            raise ContentDiscoveryError(f"Failed to discover markdown files: {str(e)}")
        
        # Set up directory structure
        try:
            first_dirpath = markdown_files[0][0]
            content_dir_path, template_dir = setup_directory_structure(content_app, first_dirpath)
        except Exception as e:
            error_message = f"Failed to set up directory structure: {str(e)}"
            self.reporter.error(f"Directory setup error: {str(e)}")
            self.reporter.write(
                "Check that the content app exists and is correctly configured in your Django project."
            )
            logger.error(f"Directory setup error: {str(e)}", exc_info=True)
            raise ConfigurationError(error_message)
        
        # Initialize processor
        try:
            processor = MarkdownProcessor(
                content_app=content_app,
                source_path=md_path,
                content_dir_path=content_dir_path,
                template_dir=template_dir,
                url_prefix=md_url_prefix,
                base_template=base_template,
                reporter=self.reporter
            )
        except Exception as e:
            logger.error(f"Error initializing markdown processor: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to initialize markdown processor: {str(e)}")
        
        # Build TOC
        try:
            self.reporter.write("Building table of contents...")
            complete_toc = processor.build_toc()
        except Exception as e:
            self.reporter.warning(
                f"Error building table of contents: {str(e)}. "
                "Processing will continue but navigation links may not work correctly."
                )
            logger.warning(f"TOC building error: {str(e)}", exc_info=True)
            complete_toc = {}
        
        # Process each file
        processed_files = []
        error_files = []
        
        for i, (dirpath, filename) in enumerate(markdown_files):
            file_path = os.path.join(dirpath, filename)
            self.reporter.write(f"Processing file {i+1}/{len(markdown_files)}: {filename}")
            
            try:
                processed_file = processor.process_file(dirpath, filename, complete_toc)
                
                if processed_file:
                    processed_files.append(processed_file)
                else:
                    error_files.append(file_path)
                    self.reporter.warning(f"File not processed: {filename}")
                    
            except Exception as e:
                error_files.append(file_path)
                error_message = f"Error processing file {filename}: {str(e)}"
                self.reporter.error(error_message)
                logger.error(f"File processing error: {str(e)}", exc_info=True)
                if not self.continue_on_error:
                    raise ProcessingError(f"Failed to process file {filename}: {str(e)}")
        
        # Generate URLs and views
        if processed_files:
            try:
                self.reporter.write("Generating URLs and views...")
                processor.generate_urls_and_views(processed_files, complete_toc)
            except Exception as e:
                error_message = f"Error generating URLs and views: {str(e)}"
                self.reporter.error(error_message)
                logger.error(f"URL and view generation error: {str(e)}", exc_info=True)
                raise OutputGenerationError(f"Failed to generate URLs and views: {str(e)}")
            self.reporter.success(
                f"Successfully processed {len(processed_files)} files for {content_app}"
                )
            
            if error_files:
                self.reporter.warning(
                    f"Note: {len(error_files)} files could not be processed: "
                    f"{', '.join(os.path.basename(f) for f in error_files[:5])}"
                    f"{' and more...' if len(error_files) > 5 else ''}"
                )
        else:
            error_message = f"No markdown files were processed successfully for {content_app}"
            self.reporter.error(error_message)
            self.reporter.write(
                "Check the markdown syntax and structure of your files, and ensure all required SpellBlocks are available."
            )
            raise ProcessingError(error_message)
        
        return len(processed_files)
    
    def discover_spellblocks(self) -> int:
        '''
        Discover available spellblocks for use in markdown processing.
        '''
        try:
            discover_blocks(self.reporter)
        except Exception as e:
            self.reporter.warning(
                f"Error during block discovery: {str(e)}. "
                "Processing will continue but some content may not render correctly."
                )
            logger.warning(f"Block discovery error: {str(e)}", exc_info=True)
            
    def validate_settings(self) -> Tuple[List[Path], List[str], List[str], List[Optional[str]]]:
        '''
        Validate the Django settings required for spellbook markdown processing.
        
        returns:
            Tuple[List[Path], List[str], List[str], List[Optional[str]]]: md_paths, md_apps, md_url_prefix, base_templates
            
        raises:
            ConfigurationError: If any settings are missing or invalid
        '''
        try:
            md_file_paths, content_apps, md_url_prefix, base_templates = validate_spellbook_settings()
        except Exception as e:
            error_message = f"Configuration error: {str(e)}"
            self.reporter.error(error_message)
            self.reporter.write(
                "Please check your Django settings.py file and ensure "
                "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP are correctly configured."
            )
            logger.error(f"Settings validation error: {str(e)}", exc_info=True)
            raise ConfigurationError(f"Settings validation failed: {str(e)}")
        
        return md_file_paths, content_apps, md_url_prefix, base_templates
    
    def process_each_source_pair(
        self, 
        md_file_paths: List[Path], 
        content_apps: List[str],
        md_url_prefix: List[str],
        base_templates: List[Optional[str]]
    ) -> List[Tuple[str, str, str, str, bool, int]]:
        '''
        Process each source-destination pair.
        
        Args:
            md_file_paths (List[Path]): List of paths to markdown files
            content_apps (List[str]): List of content app names
            md_url_prefix (List[str]): List of URL prefixes for the content app
            base_templates (List[Optional[str]]): List of base templates
        
        returns:
            List[Tuple[str, str, str, str, bool, int]]: List of tuples containing
                (md_path, content_app, url_prefix, base_template, success, processed_count)
                
        raises:
            ProcessingError: If there is an error processing a source-destination pair
        '''
        # begin with an empty list of results
        pair_results: List[Tuple[str, str, str, str, bool, int]] = []
        for i, (md_path, content_app, url_prefix, base_template) in enumerate(zip(md_file_paths, content_apps, md_url_prefix, base_templates)):
            pair_name = f"pair {i+1}/{len(md_file_paths)}: {md_path} → {content_app}"
            
            # Use the original output format for backward compatibility with tests
            self.reporter.success(f"Processing source-destination {pair_name}")

            
            # Log the URL prefix separately for new functionality
            self.reporter.write(f"Using URL prefix: '{url_prefix}'")
            base_template_doc_help_text = f"Using base template: '{base_template}'"
            if base_template is None:
                base_template_doc_help_text = "Default template will be used if not specified. Visit https://django-spellbook.org/docs/Commands/spellbook_md/ for more information."
            self.reporter.write(f"{base_template_doc_help_text}")
                
            try:
                processed_count = self._process_source_destination_pair(md_path, content_app, url_prefix, base_template)
                pair_results.append((md_path, content_app, url_prefix, True, processed_count))            
            except Exception as e:
                error_message = f"Error processing {pair_name}: {str(e)}"
                self.reporter.error(error_message)
                # Always use 0 as the count for failed pairs to avoid None
                pair_results.append((md_path, content_app, url_prefix, False, 0))
                logger.error(f"Error processing {pair_name}: {str(e)}", exc_info=True)
                
                if len(md_file_paths) > 1:
                    self.reporter.write("Continuing with next pair...")
                    continue
                else:
                    raise
        return pair_results
        
    def summary_report(self, pair_results: List[Tuple[str, str, str, bool, int]]):
        '''
        Output a summary report of the processing results.
        
        Args:
            pair_results: List of tuples containing (md_path, content_app, url_prefix, success, processed_count)
        '''
        self.reporter.generate_summary_report(pair_results)