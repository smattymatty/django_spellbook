"""
CSS generation utilities for Django Spellbook's theme system.
"""

from typing import Dict, Optional, Any
from .core import SpellbookTheme


def _is_dark_color(color: str) -> bool:
    """
    Determine if a color is dark based on its luminance.
    
    Args:
        color: Hex color string
        
    Returns:
        True if the color is dark
    """
    # Remove '#' if present
    color = color.lstrip('#')
    
    # Convert to RGB
    try:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    except (ValueError, IndexError):
        # Default to light if can't parse
        return False
    
    # Calculate relative luminance
    # Using simplified formula
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # Consider dark if luminance is below 0.5
    return luminance < 0.5


def _generate_dark_alert_variables(declarations: Dict[str, str]) -> Dict[str, str]:
    """
    Generate alert-specific CSS variables for dark mode.
    
    Args:
        declarations: Existing CSS variable declarations
        
    Returns:
        Dictionary of alert CSS variables
    """
    alert_vars = {}
    bg_color = declarations.get('--background-color', '#1a1a1a')
    
    # Alert types and their corresponding color variables
    alert_types = [
        ('info', '--info-color'),
        ('success', '--success-color'),
        ('warning', '--warning-color'),
        ('error', '--error-color'),
        ('danger', '--error-color'),  # danger uses error color
        ('primary', '--primary-color'),
        ('secondary', '--secondary-color'),
    ]
    
    for alert_type, color_var in alert_types:
        base_color = declarations.get(color_var)
        if base_color:
            # For dark mode, mix with dark background instead of white
            # and use higher opacity for better visibility
            alert_vars[f'--alert-{alert_type}-bg'] = f'color-mix(in srgb, {base_color} 20%, {bg_color})'
            alert_vars[f'--alert-{alert_type}-border'] = f'color-mix(in srgb, {base_color} 40%, {bg_color})'
            alert_vars[f'--alert-{alert_type}-text'] = f'color-mix(in srgb, {base_color} 90%, white)'
    
    return alert_vars


def _generate_prism_variables(declarations: Dict[str, str], is_dark_mode: bool) -> Dict[str, str]:
    """
    Generate Prism.js-specific CSS variables based on theme mode.
    
    Args:
        declarations: Existing CSS variable declarations
        is_dark_mode: Whether the theme is in dark mode
        
    Returns:
        Dictionary of Prism CSS variables
    """
    prism_vars = {}
    
    # Get base colors
    surface_color = declarations.get('--surface-color', '#f9fafb' if not is_dark_mode else '#1a1a1a')
    background_color = declarations.get('--background-color', '#ffffff' if not is_dark_mode else '#0d1117')
    text_color = declarations.get('--text-color', '#1f2937' if not is_dark_mode else '#e6edf3')
    text_secondary = declarations.get('--text-secondary-color', '#6b7280' if not is_dark_mode else '#8b949e')
    
    # Get theme colors
    primary = declarations.get('--primary-color', '#3b82f6')
    secondary = declarations.get('--secondary-color', '#6b7280')
    accent = declarations.get('--accent-color', '#f59e0b')
    success = declarations.get('--success-color', '#16a34a')
    warning = declarations.get('--warning-color', '#f59e0b')
    error = declarations.get('--error-color', '#dc2626')
    info = declarations.get('--info-color', '#2563eb')
    neutral = declarations.get('--neutral-color', '#9ca3af')
    emphasis = declarations.get('--emphasis-color', '#8b5cf6')
    
    # Base colors
    prism_vars['--prism-text'] = text_color
    prism_vars['--prism-selection'] = f'color-mix(in srgb, {primary} 25%, transparent)'
    
    if is_dark_mode:
        # Dark mode: slightly lighter background for contrast
        prism_vars['--prism-code-bg'] = f'color-mix(in srgb, {surface_color} 90%, {neutral})'
        prism_vars['--prism-inline-bg'] = f'color-mix(in srgb, {surface_color} 70%, {background_color})'
        prism_vars['--prism-border'] = f'color-mix(in srgb, {neutral} 25%, transparent)'
        prism_vars['--prism-shadow'] = '0 2px 8px color-mix(in srgb, black 40%, transparent)'
        
        # Token colors - slightly brighter for dark mode
        prism_vars['--prism-comment'] = f'color-mix(in srgb, {text_secondary} 70%, {neutral})'
        prism_vars['--prism-keyword'] = f'color-mix(in srgb, {primary} 80%, white)'
        prism_vars['--prism-string'] = f'color-mix(in srgb, {success} 85%, white)'
        prism_vars['--prism-function'] = f'color-mix(in srgb, {info} 85%, white)'
        prism_vars['--prism-function-name'] = info
        prism_vars['--prism-number'] = f'color-mix(in srgb, {warning} 90%, white)'
        prism_vars['--prism-property'] = f'color-mix(in srgb, {secondary} 75%, white)'
        prism_vars['--prism-operator'] = f'color-mix(in srgb, {accent} 85%, white)'
        prism_vars['--prism-punctuation'] = f'color-mix(in srgb, {neutral} 90%, white)'
        prism_vars['--prism-tag'] = error
        
        # Line numbers and highlights
        prism_vars['--prism-line-number'] = f'color-mix(in srgb, {text_secondary} 60%, transparent)'
        prism_vars['--prism-line-number-border'] = f'color-mix(in srgb, {neutral} 20%, transparent)'
        prism_vars['--prism-line-highlight'] = f'color-mix(in srgb, {primary} 10%, transparent)'
    else:
        # Light mode: slightly darker background for contrast
        prism_vars['--prism-code-bg'] = f'color-mix(in srgb, {surface_color} 95%, {neutral})'
        prism_vars['--prism-inline-bg'] = surface_color
        prism_vars['--prism-border'] = f'color-mix(in srgb, {neutral} 15%, transparent)'
        prism_vars['--prism-shadow'] = '0 2px 4px color-mix(in srgb, black 10%, transparent)'
        
        # Token colors - normal brightness for light mode
        prism_vars['--prism-comment'] = text_secondary
        prism_vars['--prism-keyword'] = primary
        prism_vars['--prism-string'] = success
        prism_vars['--prism-function'] = info
        prism_vars['--prism-function-name'] = info
        prism_vars['--prism-number'] = warning
        prism_vars['--prism-property'] = secondary
        prism_vars['--prism-operator'] = accent
        prism_vars['--prism-punctuation'] = neutral
        prism_vars['--prism-tag'] = error
        
        # Line numbers and highlights
        prism_vars['--prism-line-number'] = f'color-mix(in srgb, {text_secondary} 70%, transparent)'
        prism_vars['--prism-line-number-border'] = f'color-mix(in srgb, {neutral} 15%, transparent)'
        prism_vars['--prism-line-highlight'] = f'color-mix(in srgb, {primary} 8%, transparent)'
    
    # Diff colors (same for both modes)
    prism_vars['--prism-inserted'] = success
    prism_vars['--prism-inserted-bg'] = f'color-mix(in srgb, {success} 15%, transparent)'
    prism_vars['--prism-deleted'] = error
    prism_vars['--prism-deleted-bg'] = f'color-mix(in srgb, {error} 15%, transparent)'
    
    # Toolbar/UI elements
    prism_vars['--prism-toolbar-button-bg'] = primary
    prism_vars['--prism-toolbar-button-hover'] = f'color-mix(in srgb, {primary} 80%, black)'
    prism_vars['--prism-language-label'] = text_secondary
    prism_vars['--prism-language-label-bg'] = f'color-mix(in srgb, {neutral} 15%, transparent)'
    
    # Scrollbar
    prism_vars['--prism-scrollbar-track'] = f'color-mix(in srgb, {neutral} 10%, transparent)'
    prism_vars['--prism-scrollbar-thumb'] = f'color-mix(in srgb, {neutral} 30%, transparent)'
    prism_vars['--prism-scrollbar-thumb-hover'] = f'color-mix(in srgb, {neutral} 50%, transparent)'
    
    return prism_vars


def _generate_card_variables(declarations: Dict[str, str], is_dark_mode: bool) -> Dict[str, str]:
    """
    Generate card-specific CSS variables based on theme mode.
    
    Args:
        declarations: Existing CSS variable declarations
        is_dark_mode: Whether the theme is in dark mode
        
    Returns:
        Dictionary of card CSS variables
    """
    card_vars = {}
    
    # Get base colors
    surface_color = declarations.get('--surface-color', '#f9fafb' if not is_dark_mode else '#1a1a1a')
    neutral_color = declarations.get('--neutral-color', '#9ca3af')
    text_color = declarations.get('--text-color', '#1f2937' if not is_dark_mode else '#e6edf3')
    
    # Card backgrounds
    card_vars['--card-bg'] = surface_color
    
    if is_dark_mode:
        # Dark mode: subtle lighter backgrounds for headers/footers
        card_vars['--card-header-bg'] = f'color-mix(in srgb, {neutral_color} 15%, {surface_color})'
        card_vars['--card-footer-bg'] = f'color-mix(in srgb, {neutral_color} 15%, {surface_color})'
        card_vars['--card-border'] = f'color-mix(in srgb, {neutral_color} 30%, transparent)'
        card_vars['--card-header-border'] = f'color-mix(in srgb, {neutral_color} 35%, transparent)'
        card_vars['--card-footer-border'] = f'color-mix(in srgb, {neutral_color} 35%, transparent)'
        card_vars['--card-shadow'] = '0 0.125rem 0.25rem color-mix(in srgb, black 30%, transparent)'
        card_vars['--card-shadow-hover'] = '0 0.5rem 1rem color-mix(in srgb, black 40%, transparent)'
    else:
        # Light mode: subtle darker backgrounds for headers/footers
        card_vars['--card-header-bg'] = f'color-mix(in srgb, {neutral_color} 5%, {surface_color})'
        card_vars['--card-footer-bg'] = f'color-mix(in srgb, {neutral_color} 5%, {surface_color})'
        card_vars['--card-border'] = f'color-mix(in srgb, {neutral_color} 15%, transparent)'
        card_vars['--card-header-border'] = f'color-mix(in srgb, {neutral_color} 20%, transparent)'
        card_vars['--card-footer-border'] = f'color-mix(in srgb, {neutral_color} 20%, transparent)'
        card_vars['--card-shadow'] = '0 0.125rem 0.25rem color-mix(in srgb, black 7.5%, transparent)'
        card_vars['--card-shadow-hover'] = '0 0.5rem 1rem color-mix(in srgb, black 15%, transparent)'
    
    # Text colors
    card_vars['--card-title-color'] = text_color
    card_vars['--card-text-color'] = text_color
    
    return card_vars


def generate_css_variables(theme_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate CSS variable declarations from a theme configuration.
    
    Args:
        theme_config: Theme configuration dictionary from Django settings
        
    Returns:
        CSS string containing variable declarations
    """
    # Create theme instance
    theme = SpellbookTheme(theme_config)
    
    # Get all CSS declarations
    declarations = theme.to_css_declarations()
    
    # Add border-radius variables (non-color styling variables)
    border_radius_vars = {
        '--sb-border-radius-sm': '0.125rem',
        '--sb-border-radius-md': '0.375rem',
        '--sb-border-radius-lg': '0.5rem',
        '--sb-border-radius-xl': '0.75rem',
        '--sb-border-radius-2xl': '1rem',
    }
    declarations.update(border_radius_vars)
    
    # Add alert-specific CSS variables for dark mode
    # Determine if we're in dark mode based on background color
    bg_color = declarations.get('--background-color', '#ffffff')
    is_dark_mode = _is_dark_color(bg_color)
    
    if is_dark_mode:
        # Dark mode: mix with dark background instead of white
        alert_vars = _generate_dark_alert_variables(declarations)
    else:
        # Light mode: use default (mixing with white)
        alert_vars = {}
    
    declarations.update(alert_vars)
    
    # Add card-specific CSS variables
    card_vars = _generate_card_variables(declarations, is_dark_mode)
    declarations.update(card_vars)
    
    # Add Prism.js-specific CSS variables
    prism_vars = _generate_prism_variables(declarations, is_dark_mode)
    declarations.update(prism_vars)
    
    # Build CSS string
    css_lines = [':root {']
    
    # Sort declarations for consistent output
    for var_name in sorted(declarations.keys()):
        value = declarations[var_name]
        css_lines.append(f'  {var_name}: {value};')
    
    css_lines.append('}')
    
    return '\n'.join(css_lines)


def generate_theme_css(theme_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate complete theme CSS including variables and any additional styles.
    
    Args:
        theme_config: Theme configuration dictionary from Django settings
        
    Returns:
        Complete CSS string for the theme
    """
    css_parts = []
    
    # Generate CSS variables
    css_parts.append(generate_css_variables(theme_config))
    
    # Future: Add dark mode support
    if theme_config and theme_config.get('dark_mode'):
        css_parts.append(generate_dark_mode_css(theme_config))
    
    return '\n\n'.join(css_parts)


def generate_dark_mode_css(theme_config: Dict[str, Any]) -> str:
    """
    Generate dark mode CSS overrides.
    
    Args:
        theme_config: Theme configuration with dark mode settings
        
    Returns:
        CSS string for dark mode
    """
    # Placeholder for future dark mode implementation
    return """
/* Dark mode support - coming soon */
@media (prefers-color-scheme: dark) {
  :root {
    /* Dark mode color overrides will go here */
  }
}

[data-theme="dark"] {
  /* Manual dark mode toggle support */
}
"""


def generate_inline_theme_style(theme_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a complete <style> tag with theme CSS for inline inclusion.
    
    Args:
        theme_config: Theme configuration dictionary from Django settings
        
    Returns:
        HTML style tag containing theme CSS
    """
    css_content = generate_theme_css(theme_config)
    return f'<style id="spellbook-theme">\n{css_content}\n</style>'


def export_theme_to_json(theme_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Export theme configuration to a JSON-serializable dictionary.
    
    Args:
        theme_config: Theme configuration dictionary
        
    Returns:
        JSON-serializable theme dictionary
    """
    theme = SpellbookTheme(theme_config)
    return theme.to_dict()


def validate_theme_config(theme_config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a theme configuration dictionary.
    
    Args:
        theme_config: Theme configuration to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check structure
    if not isinstance(theme_config, dict):
        errors.append("Theme configuration must be a dictionary")
        return False, errors
    
    # Validate colors if present
    if 'colors' in theme_config:
        if not isinstance(theme_config['colors'], dict):
            errors.append("'colors' must be a dictionary")
        else:
            from .validator import validate_color
            for name, value in theme_config['colors'].items():
                try:
                    validate_color(value)
                except ValueError as e:
                    errors.append(f"Color '{name}': {str(e)}")
    
    # Validate custom colors if present
    if 'custom_colors' in theme_config:
        if not isinstance(theme_config['custom_colors'], dict):
            errors.append("'custom_colors' must be a dictionary")
        else:
            from .validator import validate_color
            for name, value in theme_config['custom_colors'].items():
                try:
                    validate_color(value)
                except ValueError as e:
                    errors.append(f"Custom color '{name}': {str(e)}")
    
    # Validate boolean flags
    if 'generate_variants' in theme_config:
        if not isinstance(theme_config['generate_variants'], bool):
            errors.append("'generate_variants' must be a boolean")
    
    if 'dark_mode' in theme_config:
        if not isinstance(theme_config['dark_mode'], bool):
            errors.append("'dark_mode' must be a boolean")
    
    return len(errors) == 0, errors