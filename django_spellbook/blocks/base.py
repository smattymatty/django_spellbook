from typing import Dict, Any, Set, Optional
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
import markdown
from logging import getLogger

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter


logger = getLogger(__name__)

class BasicSpellBlock:
    """
    Base class for spell blocks that render markdown content with specific templates.
    Now uses the custom MarkdownParser for more consistent processing.
    """

    def __init__(self, reporter: MarkdownReporter, content=None, spellbook_parser=None, **kwargs):
        self.content = content
        self.kwargs = kwargs
        self.name = getattr(self, 'name', None)
        self.template = getattr(self, 'template', None)
        self.required_kwargs = getattr(self, 'required_kwargs', set())
        self.optional_kwargs = getattr(self, 'optional_kwargs', set())
        self.reporter = reporter
        self.spellbook_parser = spellbook_parser # for nested parsing

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

        from django_spellbook.parsers import render_spellbook_markdown_to_html
        return render_spellbook_markdown_to_html(
            self.content, 
            self.reporter, 
            self.spellbook_parser
            )

    def render(self) -> str:
        """
        Render the block using its template and context.
        """
        if not self.template:
            raise ValueError(f"No template specified for block {self.name}")
        context = self.get_context()
        self.reporter.record_spellblock_usage(self.name, success=True, params=context)
        return render_to_string(self.template, context)
