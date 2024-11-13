# django_spellbook/management/commands/spellbook_md.py

import os
import datetime
import logging
import importlib
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps
from django.template.loader import render_to_string
from django_spellbook.markdown.parser import MarkdownParser
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.markdown.toc import TOCGenerator
from django_spellbook.blocks import SpellBlockRegistry

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFile:
    """Represents a processed markdown file"""
    original_path: Path
    html_content: str
    template_path: Path
    relative_url: str
    context: SpellbookContext


class MarkdownProcessingError(Exception):
    """Custom exception for markdown processing errors"""
    pass


class MarkdownFileProcessor:
    def __init__(self):
        self.parser = MarkdownParser

    def process_file(self, file_path: Path, dirpath: str, filename: str, folders: List[str]) -> Optional[ProcessedFile]:
        try:
            file_path = Path(dirpath) / filename

            # Read and parse markdown
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()

                # Parse front matter
                frontmatter = FrontMatterParser(md_text, file_path)

                # Parse markdown content
                parser = self.parser(frontmatter.raw_content)
                html_content = parser.get_html()

                # Calculate relative URL
                relative_url = str(file_path.relative_to(
                    Path(settings.SPELLBOOK_MD_PATH)
                ).with_suffix('')).replace('\\', '/')

                # Create context
                context = frontmatter.get_context(relative_url)

                return html_content, file_path, context

            except Exception as e:
                raise MarkdownProcessingError(str(e))

        except MarkdownProcessingError:
            raise
        except Exception as e:
            raise MarkdownProcessingError(
                f"Unexpected error processing {filename}: {str(e)}")


class TemplateGenerator:
    """Handles template creation and management"""

    def __init__(self, content_app: str, template_dir: str):
        self.content_app = content_app
        self.template_dir = template_dir

    def create_template(self, template_path: Path, html_content: str):
        """Create a template file with the processed HTML content"""
        try:
            template_path.parent.mkdir(parents=True, exist_ok=True)

            base_template = getattr(
                settings, 'SPELLBOOK_MD_BASE_TEMPLATE', None)

            if base_template:
                if not base_template.endswith('.html'):
                    base_template += '.html'
                final_content = (
                    "{{% extends '{}' %}}\n\n"
                    "{{% block spellbook_md %}}\n"
                    "{}\n"
                    "{{% endblock %}}"
                ).format(base_template, html_content)
            else:
                final_content = html_content

            template_path.write_text(final_content)
        except Exception as e:
            raise CommandError(
                f"Could not create template {template_path}\n {e}")

    def get_template_path(self, filename: str, folders: List[str]) -> Path:
        """Calculate the template path for a processed file"""
        folder_string = ""
        for folder in reversed(folders):
            folder_string = Path(folder_string) / folder

        return Path(self.template_dir) / folder_string / filename.replace('.md', '.html')


class URLViewGenerator:
    """Handles URL and view generation"""

    def __init__(self, content_app: str, content_dir_path: str):
        self.content_app = content_app
        self.content_dir_path = content_dir_path
        self.spellbook_dir = os.path.join(os.path.dirname(__file__), '../..')
        self._ensure_urls_views_files()

    def _ensure_urls_views_files(self):
        """Ensure URLs and views files exist in django_spellbook"""
        for file_name in ['urls.py', 'views.py']:
            file_path = os.path.join(self.spellbook_dir, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    initial_content = self._get_initial_content(file_name)
                    f.write(initial_content)
                logger.debug(f"Created new file: {file_path}")

    def _get_initial_content(self, file_name: str) -> str:
        """Get initial content for new files"""
        if file_name == 'urls.py':
            return """from django.urls import path
from . import views

urlpatterns = []
"""
        else:  # views.py
            return """
from django.shortcuts import render
"""

    def generate_urls_and_views(self, processed_files: List[ProcessedFile], toc: Dict):
        urls = []
        views = []

        for processed_file in processed_files:
            url_pattern = processed_file.relative_url
            view_name = f"view_{url_pattern.replace('/', '_').replace('.', '_')}"

            template_path = os.path.join(
                self.content_app, 'spellbook_md', url_pattern + '.html')

            urls.append(
                f"path('{url_pattern}', views.{view_name}, name='{view_name}')")
            views.append(self._generate_view_function(
                view_name, template_path, processed_file.context))

        self._write_urls(urls)
        self._write_views(views, toc)

    def _generate_view_function(self, view_name: str, template_path: str, context: SpellbookContext) -> str:
        # Create a new context dict without the TOC
        context_dict = context.__dict__.copy()
        del context_dict['toc']  # Remove the existing toc
        context_dict = {k: repr(v) if isinstance(v, (datetime.datetime, datetime.date)) else v
                        for k, v in context_dict.items()}

        return f"""
def {view_name}(request):
    context = {context_dict}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, '{template_path}', context)
"""

    def _write_urls(self, urls: List[str]):
        try:
            urls_file = os.path.join(self.spellbook_dir, 'urls.py')
            content = """from django.urls import path
from . import views

urlpatterns = [
    {}
]""".format(',\n    '.join(urls))

            with open(urls_file, 'w') as f:
                f.write(content)

        except Exception as e:
            raise CommandError(f"Failed to write URLs file: {str(e)}")

    def _write_views(self, views: List[str], toc: Dict):
        try:
            views_file = os.path.join(self.spellbook_dir, 'views.py')

            # Use the passed TOC
            content = """import datetime
from django.shortcuts import render

# Table of Contents for all views
TOC = {toc}

{views}""".format(
                toc=toc,
                views='\n'.join(views)
            )

            with open(views_file, 'w') as f:
                f.write(content)

        except Exception as e:
            raise CommandError(f"Failed to write views file: {str(e)}")


class Command(BaseCommand):
    help = "Converts markdown to html, with a spellbook twist"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.md_file_path = settings.SPELLBOOK_MD_PATH
        self.content_app = settings.SPELLBOOK_CONTENT_APP
        self.content_dir_path = ""
        self.template_dir = ""
        self.toc_generator = TOCGenerator()

        # Initialize processors
        self.discover_blocks()  # Add this line
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
            self.stdout.write("Starting spellbook_md command...")

            # Validate settings first
            self.validate_settings()

            # Discover blocks
            self.discover_blocks()

            processed_files = []

            # First pass: Build complete TOC
            self.stdout.write("Building table of contents...")
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
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise CommandError(f"Missing required setting: {setting}")
