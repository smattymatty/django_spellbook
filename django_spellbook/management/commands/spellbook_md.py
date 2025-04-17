import os
import logging
from typing import List, Dict, Tuple
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

logger = logging.getLogger(__name__)

# Custom Exception Classes
class SpellbookMDError(CommandError):
    """Base exception for all Spellbook MD errors."""
    pass

class ConfigurationError(SpellbookMDError):
    """Error related to configuration issues (settings, paths, etc.)."""
    pass

class ContentDiscoveryError(SpellbookMDError):
    """Error related to finding and parsing content files."""
    pass

class ProcessingError(SpellbookMDError):
    """Error during markdown processing."""
    pass

class OutputGenerationError(SpellbookMDError):
    """Error generating templates, views, or URLs."""
    pass

class Command(BaseCommand):
    help = "Converts markdown to html, with a spellbook twist"

    def add_arguments(self, parser):
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue processing files even if some fail'
        )

    def handle(self, *args, **options):
        """Process markdown files from all configured source-destination pairs."""
        self.continue_on_error = options.get('continue_on_error', False)
        
        try:
            # Discover spell blocks
            try:
                block_count = discover_blocks(self.stdout)
                self.stdout.write(f"Discovered {block_count} SpellBlocks")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Error during block discovery: {str(e)}. "
                        "Processing will continue but some content may not render correctly."
                    )
                )
                logger.warning(f"Block discovery error: {str(e)}", exc_info=True)
            
            # Validate settings
            try:
                md_file_paths, content_apps = validate_spellbook_settings()
            except Exception as e:
                error_message = f"Configuration error: {str(e)}"
                self.stdout.write(self.style.ERROR(error_message))
                self.stdout.write(
                    "Please check your Django settings.py file and ensure "
                    "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP are correctly configured."
                )
                logger.error(f"Settings validation error: {str(e)}", exc_info=True)
                raise ConfigurationError(f"Settings validation failed: {str(e)}")
            
            # Process each source-destination pair
            pair_results = []
            for i, (md_path, content_app) in enumerate(zip(md_file_paths, content_apps)):
                pair_name = f"pair {i+1}/{len(md_file_paths)}: {md_path} → {content_app}"
                self.stdout.write(
                    self.style.SUCCESS(f"Processing source-destination {pair_name}")
                )
                
                try:
                    processed_count = self._process_source_destination_pair(md_path, content_app)
                    pair_results.append((md_path, content_app, True, processed_count))
                except Exception as e:
                    error_message = f"Error processing {pair_name}: {str(e)}"
                    self.stdout.write(self.style.ERROR(error_message))
                    # Always use 0 as the count for failed pairs to avoid None
                    pair_results.append((md_path, content_app, False, 0))
                    logger.error(f"Error processing {pair_name}: {str(e)}", exc_info=True)
                    
                    if len(md_file_paths) > 1:
                        self.stdout.write("Continuing with next pair...")
                        continue
                    else:
                        raise
            
            # Summary report
            self.stdout.write("\nProcessing Summary:")
            success_count = sum(1 for _, _, success, _ in pair_results if success)
            total_processed = sum(count for _, _, success, count in pair_results if success)
            
            if success_count == len(pair_results):
                self.stdout.write(self.style.SUCCESS(
                    f"All {len(pair_results)} source-destination pairs processed successfully. "
                    f"Total files processed: {total_processed}."
                ))
            else:
                failed_pairs = [(src, dst) for src, dst, success, _ in pair_results if not success]
                self.stdout.write(self.style.WARNING(
                    f"{success_count} of {len(pair_results)} pairs processed successfully. "
                    f"Total files processed: {total_processed}. "
                    f"Failed pairs: {', '.join(f'{src} → {dst}' for src, dst in failed_pairs)}"
                ))
                
        except Exception as e:
            error_message = f"Command failed: {str(e)}"
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(f"Command failed: {str(e)}", exc_info=True)
            raise

    def _process_source_destination_pair(self, md_path, content_app):
        """Process all markdown files for a single source-destination pair."""
        # Find markdown files
        try:
            markdown_files = find_markdown_files(md_path)
            
            if not markdown_files:
                error_message = f"No markdown files found in {md_path}"
                self.stdout.write(self.style.ERROR(error_message))
                self.stdout.write(
                    f"Make sure the directory exists and contains .md files."
                )
                raise ContentDiscoveryError(error_message)
                
            self.stdout.write(f"Found {len(markdown_files)} markdown files to process")
            
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
            self.stdout.write(self.style.ERROR(f"Directory setup error: {str(e)}"))
            self.stdout.write(
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
                template_dir=template_dir
            )
        except Exception as e:
            logger.error(f"Error initializing markdown processor: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to initialize markdown processor: {str(e)}")
        
        # Build TOC
        try:
            self.stdout.write("Building table of contents...")
            complete_toc = processor.build_toc()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Error building table of contents: {str(e)}. "
                    "Processing will continue but navigation links may not work correctly."
                )
            )
            logger.warning(f"TOC building error: {str(e)}", exc_info=True)
            complete_toc = {}
        
        # Process each file
        processed_files = []
        error_files = []
        
        for i, (dirpath, filename) in enumerate(markdown_files):
            file_path = os.path.join(dirpath, filename)
            self.stdout.write(f"Processing file {i+1}/{len(markdown_files)}: {filename}")
            
            try:
                processed_file = processor.process_file(dirpath, filename, complete_toc)
                
                if processed_file:
                    processed_files.append(processed_file)
                else:
                    error_files.append(file_path)
                    self.stdout.write(
                        self.style.WARNING(f"File not processed: {filename}")
                    )
                    
            except Exception as e:
                error_files.append(file_path)
                error_message = f"Error processing file {filename}: {str(e)}"
                self.stdout.write(self.style.ERROR(error_message))
                logger.error(f"File processing error: {str(e)}", exc_info=True)
                
                if not self.continue_on_error:
                    raise ProcessingError(f"Failed to process file {filename}: {str(e)}")
        
        # Generate URLs and views
        if processed_files:
            try:
                self.stdout.write("Generating URLs and views...")
                processor.generate_urls_and_views(processed_files, complete_toc)
            except Exception as e:
                error_message = f"Error generating URLs and views: {str(e)}"
                self.stdout.write(self.style.ERROR(error_message))
                logger.error(f"URL and view generation error: {str(e)}", exc_info=True)
                raise OutputGenerationError(f"Failed to generate URLs and views: {str(e)}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {len(processed_files)} files for {content_app}"
                )
            )
            
            if error_files:
                self.stdout.write(
                    self.style.WARNING(
                        f"Note: {len(error_files)} files could not be processed: "
                        f"{', '.join(os.path.basename(f) for f in error_files[:5])}"
                        f"{' and more...' if len(error_files) > 5 else ''}"
                    )
                )
        else:
            error_message = f"No markdown files were processed successfully for {content_app}"
            self.stdout.write(self.style.ERROR(error_message))
            self.stdout.write(
                "Check the markdown syntax and structure of your files, and ensure all required SpellBlocks are available."
            )
            raise ProcessingError(error_message)
        
        return len(processed_files)