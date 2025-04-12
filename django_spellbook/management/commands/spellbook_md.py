# django_spellbook/management/commands/spellbook_md.py

import os
import datetime
import logging
import importlib
from typing import List, Optional, Dict, Tuple
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps
from django.urls import reverse
from django.template.loader import render_to_string

from django_spellbook.management.commands.processing.file_processor import MarkdownFileProcessor, ProcessedFile
from django_spellbook.management.commands.processing.template_generator import TemplateGenerator
from django_spellbook.management.commands.processing.url_view_generator import URLViewGenerator
from django_spellbook.markdown.parser import MarkdownParser
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.markdown.toc import TOCGenerator
from django_spellbook.blocks import SpellBlockRegistry

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Converts markdown to html, with a spellbook twist"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize empty attributes to be populated in validate_settings()
        self.md_file_paths = None  # Will hold the list of paths
        self.content_apps = None   # Will hold the list of apps
        self.md_file_path = None   # For backward compatibility (first path)
        self.content_app = None    # For backward compatibility (first app)
        self.content_dir_path = ""
        self.template_dir = ""
        self.toc_generator = TOCGenerator()

        # Initialize processors
        self.discover_blocks()
        self.file_processor = MarkdownFileProcessor()
        self.template_generator = None
        self.url_generator = None

    def discover_blocks(self):
        """Discover and register spell blocks from all installed apps"""
        self.stdout.write("Starting block discovery...")

        for app_config in apps.get_app_configs():
            try:
                # Try to import spellblocks.py from each app
                module_path = f"{app_config.name}.spellblocks"
                self.stdout.write(f"Checking {module_path}...")

                importlib.import_module(module_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Discovered blocks from {app_config.name}")
                )

            except ImportError:
                # Skip if no spellblocks.py exists
                self.stdout.write(f"No blocks found in {app_config.name}")
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Error loading blocks from {app_config.name}: {str(e)}"
                    )
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Block discovery complete. Found {len(SpellBlockRegistry._registry)} blocks."
            )
        )

    def handle(self, *args, **options):
        """Process markdown files from all configured source-destination pairs"""
        try:
            # Validate settings first
            self.validate_settings()
            
            # Process each source-destination pair
            for i, (md_path, content_app) in enumerate(zip(self.md_file_paths, self.content_apps)):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processing source-destination pair {i+1}/{len(self.md_file_paths)}: {md_path} → {content_app}"
                    )
                )
                try:
                    self._process_source_destination_pair(md_path, content_app)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing pair {md_path} → {content_app}: {str(e)}")
                    )
                    if len(self.md_file_paths) > 1:
                        self.stdout.write("Continuing with next pair...")
                        continue
                    else:
                        raise
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Command failed: {str(e)}")
            )
            raise

    def _process_source_destination_pair(self, md_path, content_app):
        """Process all markdown files for a single source-destination pair"""
        # Reset processors for each pair
        self.file_processor = MarkdownFileProcessor()
        self.template_generator = None  
        self.url_generator = None
    
    # Set current source path on processor
        self.file_processor.current_source_path = md_path
        # Set current pair for backward compatibility with existing methods
        self.md_file_path = md_path
        self.content_app = content_app
        self.content_dir_path = ""  # Reset for each pair
        self.template_dir = ""      # Reset for each pair
        self.template_generator = None  
        self.url_generator = None       
            
        processed_files = []
        
        # Build TOC for this source path
        complete_toc = self._build_toc(content_app)
        
        # Find and process markdown files
        markdown_files = self._find_markdown_files()
        if not markdown_files:
            raise CommandError(f"No markdown files found in {md_path}")
    
        
        self.stdout.write(f"Found {len(markdown_files)} markdown files to process")
        
        # Process each file
        for i, (dirpath, filename) in enumerate(markdown_files):
            self.stdout.write(f"Processing file {i+1}/{len(markdown_files)}: {filename}")
            processed_file = self._process_markdown_file(dirpath, filename, complete_toc)
            if processed_file:
                processed_files.append(processed_file)
        
        # Generate URLs and views
        if processed_files:
            self.stdout.write("Generating URLs and views...")
            self.url_generator.generate_urls_and_views(processed_files, complete_toc)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {len(processed_files)} files for {content_app}"
                )
            )
        else:
            raise CommandError(f"No markdown files were processed successfully for {content_app}")

    def _find_markdown_files(self):
        """Find all markdown files in the current source path"""
        markdown_files = []
        for dirpath, dirnames, filenames in os.walk(self.md_file_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    markdown_files.append((dirpath, filename))
        return markdown_files

    def _process_markdown_file(self, dirpath, filename, complete_toc):
        """Process a single markdown file and return a ProcessedFile or None on failure"""
        # Setup directory structure first
        if not self.content_dir_path:
            self._setup_directory_structure(dirpath)
        
        # Initialize generators if not already set
        if not self.template_generator:
            self.template_generator = TemplateGenerator(
                self.content_app, self.template_dir)
        if not self.url_generator:
            self.url_generator = URLViewGenerator(
                content_app=self.content_app,
                content_dir_path=self.content_dir_path,
                source_path=self.md_file_path  # Add this parameter
            )
        try:
            folder_list = self._get_folder_list(dirpath)
            html_content, file_path, context = self.file_processor.process_file(
                Path(dirpath), dirpath, filename, folder_list
            )
            
            relative_path = Path(file_path).relative_to(Path(self.md_file_path))
            template_path = self.template_generator.get_template_path(
                filename, folder_list
            )
            relative_url = str(
                relative_path.with_suffix('')).replace('\\', '/')
            
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
            self.stdout.write(self.style.SUCCESS(
                f"Successfully processed {filename}"))
            
            return processed_file
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error processing {filename}: {str(e)}")
            )
            return None

    def _build_toc(self, content_app:str) -> Dict:
        """Build complete table of contents"""
        toc_generator = TOCGenerator()

        for dirpath, dirnames, filenames in os.walk(self.md_file_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    try:
                        file_path = Path(dirpath) / filename
                        relative_path = file_path.relative_to(
                            Path(self.md_file_path))
                        url = f"{content_app}:" + str(relative_path.with_suffix(
                            '')).replace('\\', '/')
                        url = url.replace('/', '_')
                        # Get title from frontmatter
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        frontmatter = FrontMatterParser(content, file_path)
                        title = frontmatter.metadata.get(
                            'title', relative_path.stem)

                        toc_generator.add_entry(relative_path, title, url)
                    except Exception as e:
                        logger.error(
                            f"Error adding TOC entry for {filename}: {str(e)}")
                        continue
        returned_toc = toc_generator.get_toc()
        return returned_toc

    def _setup_directory_structure(self, dirpath: str):
        """Set up the necessary directory structure for content processing"""
        try:
            base_path = "/".join(dirpath.split("/")[:-1])
            content_app_path = os.path.join(base_path, self.content_app)

            if not os.path.exists(content_app_path):
                raise CommandError(
                    f"Content app {self.content_app} not found in {base_path}"
                )

            self.content_dir_path = content_app_path
            self._setup_template_directory()

        except Exception as e:
            raise CommandError(f"Could not set up content dir path: {str(e)}")

    def _setup_template_directory(self):
        """Set up the template directory structure"""
        try:
            base_template_dir = Path(self.content_dir_path) / 'templates' / self.content_app / 'spellbook_md'
            base_template_dir.mkdir(parents=True, exist_ok=True)
            self.template_dir = str(base_template_dir)
        except Exception as e:
            raise CommandError(
                f"Could not create template directory {base_template_dir}: {str(e)}"
            )

    def _get_folder_list(self, dirpath: str) -> List[str]:
        """Get list of folders from dirpath relative to md_file_path"""
        logger.debug(f"Getting folder list for: {dirpath}")
        folder_split = dirpath.split("/")
        folder_list = []

        # trackers
        done = False
        n = -1
        while not done:
            dirname = folder_split[n]
            logger.debug(f"Processing dirname: {dirname}")
            if dirname == str(self.md_file_path).split("/")[-1]:
                done = True
                break
            else:
                folder_list.append(dirname)
                n -= 1

        logger.debug(f"Generated folder list: {folder_list}")
        return folder_list

    def _normalize_settings(self):
        """Convert settings to normalized lists and provide backward compatibility"""
        # Get settings values with backward compatibility
        md_path = getattr(settings, 'SPELLBOOK_MD_PATH', None)
        md_app = getattr(settings, 'SPELLBOOK_MD_APP', None)
        content_app = getattr(settings, 'SPELLBOOK_CONTENT_APP', None)
        
        # Prefer SPELLBOOK_MD_APP but fall back to SPELLBOOK_CONTENT_APP
        app_setting = md_app if md_app is not None else content_app
        
        # Show deprecation warning if using old setting name
        if md_app is None and content_app is not None:
            self.stdout.write(
                self.style.WARNING(
                    "SPELLBOOK_CONTENT_APP is deprecated, use SPELLBOOK_MD_APP instead."
                )
            )
        
        # Convert to lists if needed
        md_paths = [md_path] if isinstance(md_path, (str, Path)) else md_path
        md_apps = [app_setting] if isinstance(app_setting, str) else app_setting
        return md_paths, md_apps

    def validate_settings(self):
        """Validate required settings and support multiple source-destination pairs"""
        # Normalize settings to lists
        self.md_file_paths, self.content_apps = self._normalize_settings()
        
        # Check for missing settings
        missing_settings = []
        if not self.md_file_paths:
            missing_settings.append('SPELLBOOK_MD_PATH')
        if not self.content_apps:
            missing_settings.append('SPELLBOOK_MD_APP or SPELLBOOK_CONTENT_APP')
        
        if missing_settings:
            raise CommandError(f"Missing required settings: {', '.join(missing_settings)}")
        
        # Validate list lengths match
        if len(self.md_file_paths) != len(self.content_apps):
            raise CommandError(
                "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP must have the same number of entries"
            )
        
        # Set the first pair as current (for backward compatibility)
        self.md_file_path = self.md_file_paths[0]
        self.content_app = self.content_apps[0]
        
        # Warn if multiple pairs are defined but we're only using the first one
        if len(self.md_file_paths) > 1:
            self.stdout.write(
                self.style.WARNING(
                    "Multiple source-destination pairs detected. Currently only processing the first pair."
                )
            )
        # ensure that each string is not empty
        for md_path in self.md_file_paths:
            if not md_path:
                raise CommandError(
                    "SPELLBOOK_MD_PATH must be a non-empty string."
                )
        for app_setting in self.content_apps:
            if not app_setting:
                raise CommandError(
                    "SPELLBOOK_MD_APP must be a non-empty string."
                )