from ..views import TOC
from typing import Dict
from django import template
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured

register = template.Library()


@register.inclusion_tag('django_spellbook/tocs/sidebar_toc.html', takes_context=True)
def sidebar_toc(context) -> Dict:
    """
    Generate the table of contents for the sidebar layout.

    Args:
        context: The template context from the current view

    Returns:
        Dict containing the TOC data

    Raises:
        ImproperlyConfigured: If TOC is not found in the context
    """
    toc = context.get('toc')
    if toc is None:
        raise ImproperlyConfigured(
            "The 'toc' variable is required in the context for sidebar_toc tag"
        )
    return {'toc': toc}


@register.inclusion_tag('django_spellbook/data/metadata.html')
def show_metadata():
    """Display metadata in a formatted way"""
    pass


@register.simple_tag
def spellbook_url(url_path: str) -> str:
    """
    Convert a TOC url path to a proper Django URL.

    Args:
        url_path (str): The URL path to convert

    Returns:
        str: The reversed URL if successful, '#' otherwise

    Examples:
        >>> spellbook_url('docs/page')
        '/docs/page/'
        >>> spellbook_url('invalid/path')
        '#'
    """
    if not url_path:
        return '#'

    view_name = f"view_{url_path.replace('/', '_')}"
    try:
        return reverse(view_name)
    except NoReverseMatch:
        return '#'


@register.inclusion_tag('django_spellbook/data/styles.html')
def spellbook_styles():
    """Include the spellbook styles in the page"""
    return {}
