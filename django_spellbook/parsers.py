# django_spellbook/parsers.py
# StringIO
from io import StringIO
from .markdown.engine import SpellbookMarkdownEngine
from .management.commands.spellbook_md_p.reporter import MarkdownReporter # Or a generic reporter interface

def render_spellbook_markdown_to_html(markdown_string: str, reporter: MarkdownReporter = None, db_handler=None) -> str:
    """
    Parses markdown with SpellBlocks and returns HTML.
    Optionally handles database interactions if a db_handler is provided.
    """
    if reporter is None:
        reporter = MarkdownReporter(StringIO(), report_level='minimal') # Default to debug level

    engine = SpellbookMarkdownEngine(reporter=reporter, db_handler=db_handler)
    html_output = engine.parse_and_render(markdown_string)
    return html_output