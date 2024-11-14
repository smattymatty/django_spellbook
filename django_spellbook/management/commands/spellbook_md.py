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
        # These will be validated in handle()
        self.md_file_path = getattr(settings, 'SPELLBOOK_MD_PATH', None)
        self.content_app = getattr(settings, 'SPELLBOOK_CONTENT_APP', None)
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
        try:
            # Validate settings first
            self.validate_settings()

            processed_files = []

            # First pass: Build complete TOC
            complete_toc = self._build_toc()

            # Second pass: Process files
            self.stdout.write("Processing markdown files...")

            # Get all markdown files first
            markdown_files = []
            for dirpath, dirnames, filenames in os.walk(self.md_file_path):
                for filename in filenames:
                    if filename.endswith('.md'):
                        markdown_files.append((dirpath, filename))

            self.stdout.write(
                f"Found {len(markdown_files)} markdown files to process")

            # Process each file
            for dirpath, filename in markdown_files:
                self.stdout.write(f"Processing {filename}...")

                if not self.content_dir_path:
                    self._setup_directory_structure(dirpath)
                    self.template_generator = TemplateGenerator(
                        self.content_app, self.template_dir)
                    self.url_generator = URLViewGenerator(
                        self.content_app, self.content_dir_path)

                try:
                    folder_list = self._get_folder_list(dirpath)
                    html_content, file_path, context = self.file_processor.process_file(
                        Path(dirpath), dirpath, filename, folder_list
                    )

                    relative_path = Path(file_path).relative_to(
                        Path(self.md_file_path))
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
                    processed_files.append(processed_file)

                    self.template_generator.create_template(
                        template_path,
                        html_content
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"Successfully processed {filename}"))

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error processing {filename}: {str(e)}")
                    )
                    continue

            if processed_files:
                self.stdout.write("Generating URLs and views...")
                self.url_generator.generate_urls_and_views(
                    processed_files, complete_toc)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {len(processed_files)} files")
                )
            else:
                raise CommandError(
                    "No markdown files were processed successfully")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Command failed: {str(e)}")
            )
            raise

    def _build_toc(self) -> Dict:
        """Build complete table of contents"""
        toc_generator = TOCGenerator()

        for dirpath, dirnames, filenames in os.walk(self.md_file_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    try:
                        file_path = Path(dirpath) / filename
                        relative_path = file_path.relative_to(
                            Path(self.md_file_path))
                        url = str(relative_path.with_suffix(
                            '')).replace('\\', '/')

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

        return toc_generator.get_toc()

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
            base_template_dir = os.path.join(
                self.content_dir_path,
                f"templates/{self.content_app}/spellbook_md"
            )
            if not os.path.exists(base_template_dir):
                os.makedirs(base_template_dir)
            self.template_dir = base_template_dir
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

    def validate_settings(self):
        """Validate required settings"""
        required_settings = ['SPELLBOOK_MD_PATH', 'SPELLBOOK_CONTENT_APP']
        missing_settings = [
            setting for setting in required_settings
            if not getattr(settings, setting, None)
        ]
        if missing_settings:
            raise CommandError(
                f"Missing required settings: {', '.join(missing_settings)}")
