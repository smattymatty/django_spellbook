from typing import Dict, Any, Set
from django.template.loader import render_to_string
import markdown
from logging import getLogger

logger = getLogger(__name__)


class BasicSpellBlock:
    """
    Base class for spell blocks that render markdown content with specific templates.

    This class provides the foundation for creating custom content blocks with
    markdown processing capabilities and template rendering.
    """

    def __init__(self, content=None, **kwargs):
        """
        Initialize a spell block with content and optional parameters.

        Args:
            content (str, optional): Markdown content to be processed
            **kwargs: Additional keyword arguments for template rendering
        """
        self.content = content
        self.kwargs = kwargs
        self.name = getattr(self, 'name', None)
        self.template = getattr(self, 'template', None)
        self.required_kwargs = getattr(self, 'required_kwargs', set())
        self.optional_kwargs = getattr(self, 'optional_kwargs', set())

    def get_context(self) -> Dict[str, Any]:
        """
        Get the context dictionary for template rendering.

        Returns:
            Dict[str, Any]: Context dictionary containing processed content and kwargs
        """
        return {
            'content': self.process_content(),
            **self.kwargs
        }

    def process_content(self) -> str:
        """
        Process markdown content with standard extensions.

        Returns:
            str: Processed HTML content
        """
        if self.content is None:
            return ''

        return markdown.markdown(
            self.content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
            ]
        )

    def render(self) -> str:
        """
        Render the block using its template and context.

        Returns:
            str: Rendered HTML content

        Raises:
            ValueError: If no template is specified for the block
        """
        if not self.template:
            raise ValueError(f"No template specified for block {self.name}")

        context = self.get_context()
        return render_to_string(self.template, context)
