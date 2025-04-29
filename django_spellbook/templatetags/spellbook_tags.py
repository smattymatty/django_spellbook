from ..views import TOC
from typing import Dict
from django import template
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist

from django_spellbook.utils import remove_leading_dash
from django_spellbook.markdown.context import SpellbookContext

from .tag_utils import get_user_metadata_template, get_dev_metadata_template, get_current_app_index

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


@register.simple_tag(takes_context=True)
def show_metadata(context, display_type="for_user"):
    """
    Display metadata in a formatted way.
    
    Args:
        context: The template context
        display_type: Either 'for_user' or 'for_dev'
    
    Returns:
        Rendered HTML string
    """
    if display_type not in ['for_user', 'for_dev']:
        return f"Error: show_metadata tag requires 'for_user' or 'for_dev', got '{display_type}'"
    
    if context:
        # Get metadata from context
        metadata = context.get('metadata', {})
    else:
        metadata = {}
    
    # Get app index from context
    app_index = get_current_app_index(context)
    
    # Determine which template to use
    if display_type == 'for_user':
        template = get_user_metadata_template(app_index)
    else:  # display_type == 'for_dev'
        template = get_dev_metadata_template(app_index)
    
    # Create template context
    template_context = {
        'metadata': metadata
    }
    
    # Render the template
    try:
        return render_to_string(template, template_context)
    except TemplateDoesNotExist:
        return f"Error: Metadata template '{template}' not found"
    except Exception as e:
        return f"Error: Failed to render metadata template '{template}': {str(e)}"


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
