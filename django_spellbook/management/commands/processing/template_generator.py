from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.management.base import CommandError

from django.template.loader import render_to_string


class TemplateGenerator:
    """Handles template creation and management for markdown-generated content."""

    def __init__(self, content_app: str, template_dir: str):
        """
        Initialize the TemplateGenerator.

        Args:
            content_app (str): The Django app name where content will be stored
            template_dir (str): Base directory for templates
        """
        self.content_app = content_app
        self.template_dir = template_dir

    def create_template(self, template_path: Path, html_content: str) -> None:
        """
        Create a template file with the processed HTML content.

        Args:
            template_path (Path): Path where the template should be created
            html_content (str): Processed HTML content to be included in template

        Raises:
            CommandError: If template creation fails
        """
        try:
            self._ensure_template_directory(template_path)
            final_content = self._prepare_template_content(html_content)
            self._write_template_file(template_path, final_content)
        except Exception as e:
            raise CommandError(
                f"Could not create template {template_path}: {str(e)}")

    def get_template_path(self, filename: str, folders: list[str]) -> Path:
        """
        Calculate the template path for a processed file.

        Args:
            filename (str): Name of the markdown file
            folders (list[str]): List of folder names in the path

        Returns:
            Path: Calculated template path
        """
        folder_path = self._build_folder_path(folders)
        return Path(self.template_dir) / folder_path / self._convert_filename(filename)

    def _ensure_template_directory(self, template_path: Path) -> None:
        """Create template directory if it doesn't exist."""
        template_path.parent.mkdir(parents=True, exist_ok=True)

    def _prepare_template_content(self, html_content: str) -> str:
        """
        Prepare the final template content with proper inheritance.

        Args:
            html_content (str): The processed HTML content

        Returns:
            str: Final template content with inheritance if applicable
        """
        base_template = self._get_base_template()
        if base_template:
            return self._wrap_with_base_template(html_content, base_template)
        return html_content

    def _get_base_template(self) -> Optional[str]:
        """Get the base template name from settings."""
        base_template = getattr(settings, 'SPELLBOOK_MD_BASE_TEMPLATE', None)
        if base_template and not base_template.endswith('.html'):
            base_template += '.html'
        return base_template

    def _wrap_with_base_template(self, content: str, base_template: str) -> str:
        """Wrap content with base template inheritance."""
        return (
            "{{% extends '{}' %}}\n\n"
            "{{% block spellbook_md %}}\n"
            "{}\n"
            "{{% endblock %}}"
        ).format(base_template, content)

    def _write_template_file(self, template_path: Path, content: str) -> None:
        """Write the final content to the template file."""
        template_path.write_text(content)

    def _build_folder_path(self, folders: list[str]) -> Path:
        """Build the folder path from the list of folders."""
        folder_path = Path("")
        for folder in reversed(folders):
            folder_path = folder_path / folder
        return folder_path

    @staticmethod
    def _convert_filename(filename: str) -> str:
        """Convert markdown filename to HTML template filename."""
        return filename.replace('.md', '.html')
