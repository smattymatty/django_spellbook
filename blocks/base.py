from typing import Dict, Any, Set
from django.template.loader import render_to_string
import markdown
from logging import getLogger

logger = getLogger(__name__)


class BasicSpellBlock:
    def __init__(self, content=None, **kwargs):
        self.content = content
        self.kwargs = kwargs
        self.name = getattr(self, 'name', None)
        self.template = getattr(self, 'template', None)
        self.required_kwargs = getattr(self, 'required_kwargs', set())
        self.optional_kwargs = getattr(self, 'optional_kwargs', set())

    def get_context(self):
        return {
            'content': self.process_content(),
            **self.kwargs
        }

    def process_content(self):
        return markdown.markdown(
            self.content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
            ]
        )

    def render(self):
        if not self.template:
            raise ValueError(f"No template specified for block {self.name}")

        context = self.get_context()
        return render_to_string(self.template, context)
