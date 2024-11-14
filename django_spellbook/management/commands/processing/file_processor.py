from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from django.conf import settings
from django_spellbook.markdown.parser import MarkdownParser
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.markdown.frontmatter import FrontMatterParser


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
        """Main processing function that orchestrates the markdown processing"""
        try:
            file_path = self._validate_and_get_path(dirpath, filename)
            md_text = self._read_markdown_file(file_path)

            # Process the markdown content
            processed_content = self._process_markdown_content(
                md_text, file_path)

            # Generate file metadata
            file_metadata = self._generate_file_metadata(
                file_path, processed_content)

            return file_metadata
        except MarkdownProcessingError:
            raise
        except Exception as e:
            raise MarkdownProcessingError(
                f"Unexpected error processing {filename}: {str(e)}")

    def _validate_and_get_path(self, dirpath: str, filename: str) -> Path:
        """Validates and returns the full file path"""
        try:
            return Path(dirpath) / filename
        except Exception as e:
            raise MarkdownProcessingError(f"Invalid file path: {str(e)}")

    def _read_markdown_file(self, file_path: Path) -> str:
        """Reads and returns the content of a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise MarkdownProcessingError(
                f"Error reading file {file_path}: {str(e)}")

    def _process_markdown_content(self, md_text: str, file_path: Path) -> Tuple[str, SpellbookContext]:
        """Processes markdown content and returns HTML and context"""
        try:
            # Parse front matter
            frontmatter = FrontMatterParser(md_text, file_path)

            # Parse markdown content
            parser = self.parser(frontmatter.raw_content)
            html_content = parser.get_html()

            return html_content, frontmatter
        except Exception as e:
            raise MarkdownProcessingError(
                f"Error processing markdown: {str(e)}")

    def _generate_file_metadata(self, file_path: Path,
                                processed_content: Tuple[str, SpellbookContext]) -> Tuple[str, Path, SpellbookContext]:
        """Generates metadata for the processed file"""
        try:
            html_content, frontmatter = processed_content

            # Calculate relative URL
            relative_url = self._calculate_relative_url(file_path)

            # Create context
            context = frontmatter.get_context(relative_url)

            return html_content, file_path, context
        except Exception as e:
            raise MarkdownProcessingError(
                f"Error generating metadata: {str(e)}")

    def _calculate_relative_url(self, file_path: Path) -> str:
        """Calculates the relative URL for a file"""
        try:
            return str(file_path.relative_to(
                Path(settings.SPELLBOOK_MD_PATH)
            ).with_suffix('')).replace('\\', '/')
        except Exception as e:
            raise MarkdownProcessingError(
                f"Error calculating relative URL: {str(e)}")
