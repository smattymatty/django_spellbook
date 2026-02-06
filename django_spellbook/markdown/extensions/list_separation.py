"""
List Separation Extension for Python-Markdown
==============================================

Prevents ordered and unordered lists from merging into a single list
when they appear consecutively. Python-Markdown's default list processors
treat both ``<ol>`` and ``<ul>`` as valid siblings, causing a ``<ul>``
following an ``<ol>`` (or vice versa) to be appended to the previous list.

This extension overrides only ``SIBLING_TAGS`` on the list block processors
so each type only considers its own tag as a sibling. Unlike ``sane_lists``,
this does **not** change ``LAZY_OL`` or ``CHILD_RE`` patterns.
"""

from markdown.extensions import Extension
from markdown.blockprocessors import OListProcessor, UListProcessor


class SeparateOListProcessor(OListProcessor):
    """OListProcessor that only considers <ol> as a valid sibling, not <ul>."""
    SIBLING_TAGS = ['ol']


class SeparateUListProcessor(UListProcessor):
    """UListProcessor that only considers <ul> as a valid sibling, not <ol>."""
    SIBLING_TAGS = ['ul']


class ListSeparationExtension(Extension):
    """
    Extension that registers list processors with restricted sibling tags.
    """

    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            SeparateOListProcessor(md.parser), 'olist', 40
        )
        md.parser.blockprocessors.register(
            SeparateUListProcessor(md.parser), 'ulist', 30
        )


def makeExtension(**kwargs):
    return ListSeparationExtension(**kwargs)
