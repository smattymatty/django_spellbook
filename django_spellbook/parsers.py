# django_spellbook/parsers.py
import warnings
from io import StringIO
from .markdown.engine import SpellbookMarkdownEngine
from .management.commands.spellbook_md_p.reporter import MarkdownReporter


def spellbook_render(markdown_string: str, reporter: MarkdownReporter = None, db_handler=None) -> str:
    """
    Parse markdown with SpellBlocks and return HTML.

    Args:
        markdown_string: Markdown text to parse and render
        reporter: Optional MarkdownReporter for logging/debugging
        db_handler: Optional database handler for dynamic content

    Returns:
        HTML string rendered from the markdown input

    Example:
        >>> from django_spellbook.parsers import spellbook_render
        >>> html = spellbook_render("# Hello World")
    """
    if reporter is None:
        reporter = MarkdownReporter(StringIO(), report_level='minimal')

    engine = SpellbookMarkdownEngine(reporter=reporter, db_handler=db_handler)
    html_output = engine.parse_and_render(markdown_string)
    return html_output


def render_spellbook_markdown_to_html(markdown_string: str, reporter: MarkdownReporter = None, db_handler=None) -> str:
    """
    .. deprecated:: 0.2.4
        Use :func:`spellbook_render` instead. This function will be removed in version 0.4.0.

    Parses markdown with SpellBlocks and returns HTML.
    Optionally handles database interactions if a db_handler is provided.

    This function is deprecated. Please use ``spellbook_render()`` instead.
    """
    warnings.warn(
        "`render_spellbook_markdown_to_html` is deprecated and will be removed in version 0.4.0. "
        "Use `spellbook_render` instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return spellbook_render(markdown_string, reporter=reporter, db_handler=db_handler)