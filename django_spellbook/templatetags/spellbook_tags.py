from ..views import TOC
from typing import Dict
from django import template
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.template.base import FilterExpression, kwarg_re
from django.utils.safestring import mark_safe

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


@register.simple_tag(takes_context=True)
def directory_metadata(context, display_type="for_user"):
    """
    Display directory statistics in a formatted metadata box.

    Shows aggregate stats: total pages, direct pages, subdirectories, last updated.
    Only renders if directory_stats exists in context (directory index pages only).

    Args:
        context: Template context from directory index view
        display_type: Either 'for_user' (default) or 'for_dev'

    Returns:
        Rendered HTML string or empty string if not a directory page
    """
    if display_type not in ['for_user', 'for_dev']:
        return f"Error: directory_metadata tag requires 'for_user' or 'for_dev', got '{display_type}'"

    directory_stats = context.get('directory_stats')

    # Only render on directory index pages
    if not directory_stats:
        return ''

    # Check if we have any meaningful stats to display
    # For user view, check stats; for dev view, always show if directory_stats exists
    if display_type == 'for_user':
        has_stats = (
            directory_stats.get('total_pages', 0) > 0 or
            directory_stats.get('subdirectory_count', 0) > 0 or
            directory_stats.get('last_updated') is not None
        )

        if not has_stats:
            return ''  # Empty directory, don't show stats box

    template_context = {
        'directory_stats': directory_stats,
        'directory_name': context.get('directory_name', '')
    }

    # Select template based on display type
    if display_type == 'for_user':
        template_name = 'django_spellbook/components/directory_metadata.html'
    else:  # display_type == 'for_dev'
        template_name = 'django_spellbook/components/directory_metadata_dev.html'

    try:
        return render_to_string(template_name, template_context)
    except TemplateDoesNotExist:
        return f"Error: Directory metadata template '{template_name}' not found"
    except Exception as e:
        return f"Error: Failed to render directory metadata: {str(e)}"


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
    """
    Include the spellbook styles in the page with dynamic theme support.
    
    This tag generates CSS variables from Django settings and passes them
    to the template for inclusion before the static CSS files.
    """
    from django.conf import settings
    from django_spellbook.theme import generate_theme_css
    
    # Get theme configuration from settings
    theme_config = getattr(settings, 'SPELLBOOK_THEME', None)
    
    # Generate theme CSS variables
    # Always generate CSS (even with defaults) to ensure variables are available
    theme_css = generate_theme_css(theme_config)
    
    # Return context for the template
    return {
        'theme_css': theme_css
    }


@register.simple_tag
def dash_strip(string: str) -> str:
    """Strip the initial dashes from a string"""
    return remove_leading_dash(string)


@register.simple_tag(takes_context=True)
def page_header(context):
    """
    Display unified page header with title, author, and navigation.

    Includes:
    - Back to parent directory (if not at root)
    - Title
    - Author (if set)
    - Prev/Next navigation

    Args:
        context: The template context

    Returns:
        Rendered HTML string
    """
    if not context:
        return ""

    metadata = context.get('metadata', {})
    is_directory = context.get('is_directory_index', False)

    # Get parent directory info from context
    # Directory pages use parent_dir_url, content pages use parent_directory_url
    parent_dir_url = context.get('parent_directory_url') or context.get('parent_dir_url')
    parent_dir_name = context.get('parent_directory_name') or context.get('parent_dir_name', 'Directory')

    # For directory pages, use directory_name as title
    if is_directory:
        title = context.get('directory_name')
        # If directory_name is not set or is empty, try to extract from directory_path
        if not title:
            directory_path = context.get('directory_path', '').strip('/')
            if directory_path:
                # Get the last part of the path and humanize it
                path_parts = directory_path.split('/')
                last_part = path_parts[-1] if path_parts else ''
                if last_part:
                    title = last_part.replace('_', ' ').replace('-', ' ').title()
                else:
                    title = 'Content'
            else:
                title = 'Content'
    else:
        title = metadata.get('title')

    template_context = {
        'title': title,
        'author': metadata.get('author') if not is_directory else None,
        'prev_page': metadata.get('prev_page') if not is_directory else None,
        'next_page': metadata.get('next_page') if not is_directory else None,
        'parent_directory_url': parent_dir_url,
        'parent_directory_name': parent_dir_name,
        'parent_dir_url': context.get('parent_dir_url'),  # Also pass for directory pages
        'parent_dir_name': context.get('parent_dir_name'),
    }

    try:
        return render_to_string(
            'django_spellbook/components/page_header.html',
            template_context
        )
    except TemplateDoesNotExist:
        return "Error: Page header template not found"
    except Exception as e:
        return f"Error: Failed to render page header: {str(e)}"


@register.simple_tag(takes_context=True)
def page_metadata(context, display_type="for_user"):
    """
    Alias for show_metadata with clearer naming.
    Displays publication metadata (dates, tags, word count).

    Args:
        context: The template context
        display_type: Either 'for_user' or 'for_dev'

    Returns:
        Rendered HTML string
    """
    return show_metadata(context, display_type)


class MinimalReporter:
    """
    Minimal reporter for template tag usage.

    SpellBlocks require a reporter for statistics tracking,
    but template tags don't need this functionality.
    """
    def __init__(self):
        """Initialize with empty spellblocks list."""
        self.spellblocks = []

    def record_spellblock_usage(self, name, success=True, params=None):
        """No-op implementation of record_spellblock_usage."""
        pass

    def write(self, message, **kwargs):
        """No-op implementation of write."""
        pass

    def error(self, message, **kwargs):
        """No-op implementation of error."""
        pass

    def success(self, message, **kwargs):
        """No-op implementation of success."""
        pass


def render_spellblock_error(message):
    """
    Render a visible error for SpellBlock failures.

    Args:
        message: Error message to display

    Returns:
        Safe HTML string with error styling
    """
    return mark_safe(
        f'<div class="sb-spellblock-error sb-p-3 sb-rounded sb-border sb-bg-error-25 sb-text-error">'
        f'<strong>SpellBlock Error:</strong> {message}'
        f'</div>'
    )


@register.tag('spellblock')
def do_spellblock(parser, token):
    """
    Render a SpellBlock in a Django template.

    Usage:
        {% spellblock "alert" type="warning" %}
            <p>Content here</p>
        {% endspellblock %}

    Args:
        parser: Django template parser
        token: Current token being parsed

    Returns:
        SpellBlockTemplateNode instance

    Raises:
        TemplateSyntaxError: If block name is missing
    """
    bits = token.split_contents()
    tag_name = bits.pop(0)

    if not bits:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' requires a block name as first argument"
        )

    # Parse arguments
    args = []
    kwargs = {}
    for bit in bits:
        match = kwarg_re.match(bit)
        if match and match.group(1):
            key, value = match.groups()
            kwargs[key] = FilterExpression(value, parser)
        else:
            args.append(FilterExpression(bit, parser))

    if not args:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' requires a block name as first argument"
        )

    # Capture content until {% endspellblock %}
    nodelist = parser.parse(('endspellblock',))
    parser.delete_first_token()

    return SpellBlockTemplateNode(args[0], nodelist, kwargs)


@register.tag('endspellblock')
def do_endspellblock(parser, token):
    """
    Closing tag for spellblock.
    
    This should never actually execute - it's consumed by parser.parse() 
    in do_spellblock. Registration is required for Django's template parser.
    """
    raise template.TemplateSyntaxError(
        "Orphaned {% endspellblock %} tag found. "
        "endspellblock must be paired with a preceding {% spellblock %} tag."
    )


class SpellBlockTemplateNode(template.Node):
    """
    Template node for rendering SpellBlocks.

    Handles argument resolution, content rendering, and SpellBlock instantiation.
    """

    def __init__(self, name_expr, nodelist, kwargs):
        """
        Initialize the node.

        Args:
            name_expr: FilterExpression for block name
            nodelist: NodeList of content between tags
            kwargs: Dict of FilterExpressions for keyword arguments
        """
        self.name_expr = name_expr
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        """
        Render the SpellBlock.

        Args:
            context: Template context

        Returns:
            Rendered HTML string
        """
        # Resolve block name
        try:
            name = self.name_expr.resolve(context)
        except template.VariableDoesNotExist:
            return render_spellblock_error("Block name could not be resolved")

        # Resolve kwargs
        try:
            resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        except template.VariableDoesNotExist as e:
            return render_spellblock_error(f"Argument could not be resolved: {e}")

        # Render content
        with context.push():
            content = self.nodelist.render(context)

        # Get block from registry
        from django_spellbook.blocks import SpellBlockRegistry
        BlockClass = SpellBlockRegistry.get_block(name)

        if BlockClass is None:
            return render_spellblock_error(f"Block '{name}' not found in registry")

        # Instantiate and render block
        try:
            # Pass minimal reporter for template tag usage (no statistics tracking needed)
            reporter = MinimalReporter()
            block_instance = BlockClass(reporter=reporter, content=content, **resolved_kwargs)
            return mark_safe(block_instance.render())
        except Exception as e:
            return render_spellblock_error(f"Error rendering '{name}': {str(e)}")
