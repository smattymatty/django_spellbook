from ..views import TOC
from typing import Dict
from django import template
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured

from django_spellbook.utils import remove_leading_dash

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
    current_url = context.get('current_url')
    if toc is None:
        raise ImproperlyConfigured(
            "The 'toc' variable is required in the context for sidebar_toc tag"
        )
    return {'toc': toc, 'current_url': current_url}


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
        str: The reversed URL if successful
        
    Exceptions:
        NoReverseMatch: If the URL path is not found

    """
    try:
        if not url_path:
            return '#'
        return reverse(url_path)
    except NoReverseMatch:
        return f"{url_path} xx Not Found"


@register.inclusion_tag('django_spellbook/data/styles.html')
def spellbook_styles():
    """Include the spellbook styles in the page"""
    return {}


@register.simple_tag
def dash_strip(string: str) -> str:
    """Strip the initial dashes from a string"""
    return remove_leading_dash(string)
