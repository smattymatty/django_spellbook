from typing import Dict, Any, Set
from django.template.loader import render_to_string
import markdown
from logging import getLogger

logger = getLogger(__name__)

class BasicSpellBlock:
    """
    Base class for spell blocks that render markdown content with specific templates.
    Now uses the custom MarkdownParser for more consistent processing.
    """

    def __init__(self, content=None, **kwargs):
        self.content = content
        self.kwargs = kwargs
        self.name = getattr(self, 'name', None)
        self.template = getattr(self, 'template', None)
        self.required_kwargs = getattr(self, 'required_kwargs', set())
        self.optional_kwargs = getattr(self, 'optional_kwargs', set())

    def get_context(self) -> Dict[str, Any]:
        """
        Get the context dictionary for template rendering.
        """
        return {
            'content': self.process_content(),
            **self.kwargs
        }

    def process_content(self) -> str:
        """
        Process markdown content using our custom MarkdownParser.
        This ensures consistent processing across the entire application.
        """
        if self.content is None:
            return ''

        from django_spellbook.markdown.parser import MarkdownParser

        parser = MarkdownParser(self.content)
        return parser.get_html()

    def render(self) -> str:
        """
        Render the block using its template and context.
        """
        if not self.template:
            raise ValueError(f"No template specified for block {self.name}")

        context = self.get_context()
        return render_to_string(self.template, context)