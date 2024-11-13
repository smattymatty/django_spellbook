from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('spellbook/toc.html')
def show_toc(markdown_content):
    """Generate table of contents from markdown headers"""
    pass


@register.inclusion_tag('spellbook/metadata.html')
def show_metadata(markdown_file):
    """Display metadata in a formatted way"""
    pass


@register.simple_tag
def spellbook_url(url_path):
    """Convert a TOC url path to a proper Django URL"""
    view_name = f"view_{url_path.replace('/', '_')}"
    try:
        return reverse(view_name)
    except:
        return '#'
