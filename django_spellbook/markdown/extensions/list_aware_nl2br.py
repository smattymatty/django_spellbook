# django_spellbook/markdown/extensions/list_aware_nl2br.py
"""
List-Aware Newline-to-Break Extension for Python-Markdown
==========================================================

This is a simplified nl2br extension that is identical to the standard nl2br
but uses the name "list_aware_nl2br" for clarity in documentation.

**Important**: When using nl2br with sane_lists, you MUST include a blank line
before lists for them to render correctly. This is standard Markdown behavior.

Example (correct):
```markdown
Some text here.

- List item 1
- List item 2
```

Example (incorrect - won't work):
```markdown
Some text here.
- List item 1  ← This will NOT render as a list
- List item 2
```

Usage:
    markdown.markdown(text, extensions=[ListAwareNl2BrExtension()])
"""

from markdown.extensions import Extension
from markdown.inlinepatterns import SubstituteTagInlineProcessor

# Pattern for matching newlines (same as standard nl2br)
BR_RE = r'\n'


class ListAwareNl2BrExtension(Extension):
    """
    Extension to convert newlines to <br/> tags.

    This is functionally identical to markdown.extensions.nl2br.
    The name "list_aware" is a reminder that when using this with sane_lists,
    you must include blank lines before lists (standard Markdown requirement).
    """

    def extendMarkdown(self, md):
        """
        Register the nl2br processor with Markdown.

        Uses the same priority (5) as the standard nl2br extension.

        Args:
            md: The Markdown instance
        """
        br_tag = SubstituteTagInlineProcessor(BR_RE, 'br')
        md.inlinePatterns.register(br_tag, 'nl', 5)


def makeExtension(**kwargs):
    """
    Create and return an instance of the extension.

    This function allows the extension to be loaded by name:
    markdown.markdown(text, extensions=['list_aware_nl2br'])
    """
    return ListAwareNl2BrExtension(**kwargs)
