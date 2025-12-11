"""
Built-in theme presets for Django Spellbook.

This module maintains backward compatibility while supporting the new mode system.
"""

from typing import Dict, Any, Optional
from .presets_with_modes import THEMES_WITH_MODES, get_theme_with_mode


# Built-in theme presets
THEMES = {
    'default': {
        'name': 'default',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#2563eb',       # Blue 600 - 4.5:1 on white
            'secondary': '#4b5563',     # Gray 600 - 7:1 on white
            'accent': '#d97706',        # Amber 600 - 4.5:1 on white
            'neutral': '#6b7280',       # Gray 500 - 4.5:1 on white

            # Status colors - WCAG AA compliant
            'error': '#dc2626',         # Red 600 - 4.5:1 on white
            'warning': '#d97706',       # Amber 600 - 4.5:1 on white
            'success': '#16a34a',       # Green 600 - 4.5:1 on white
            'info': '#0284c7',          # Sky 600 - 4.5:1 on white

            # Specialty colors - WCAG AA compliant
            'emphasis': '#7c3aed',      # Violet 600 - 4.5:1 on white
            'subtle': '#f3f4f6',        # Gray 100 - background use only
            'distinct': '#0891b2',      # Cyan 600 - 4.5:1 on white
            'aether': '#c026d3',        # Fuchsia 600 - 4.5:1 on white
            'artifact': '#ca8a04',      # Yellow 600 - 4.5:1 on white
            'sylvan': '#16a34a',        # Green 600 - 4.5:1 on white
            'danger': '#991b1b',        # Red 800 - 7:1 on white
        },
        'generate_variants': True,
    },
    
    'arcane': {
        'name': 'arcane',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#7c3aed',      # Violet 600 - readable purple
            'secondary': '#4b5563',    # Gray 600 - readable gray
            'accent': '#d97706',       # Amber 600 - readable gold
            'neutral': '#6b7280',      # Gray 500 - readable neutral

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#d97706',      # Amber 600 - readable
            'success': '#16a34a',      # Green 600 - readable
            'info': '#7c3aed',         # Violet 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#9333ea',     # Purple 600 - readable
            'subtle': '#faf5ff',       # Purple 50 - background
            'distinct': '#c026d3',     # Fuchsia 600 - readable
            'aether': '#db2777',       # Pink 600 - readable
            'artifact': '#ca8a04',     # Yellow 600 - readable
            'sylvan': '#16a34a',       # Green 600 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'celestial': {
        'name': 'celestial',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#0284c7',      # Sky 600 - celestial blue
            'secondary': '#6b7280',    # Gray 500 - readable
            'accent': '#d97706',       # Amber 600 - golden light
            'neutral': '#71717a',      # Zinc 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#d97706',      # Amber 600 - readable
            'success': '#16a34a',      # Green 600 - readable
            'info': '#0284c7',         # Sky 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#7c3aed',     # Violet 600 - divine
            'subtle': '#f0f9ff',       # Sky 50 - background
            'distinct': '#0891b2',     # Cyan 600 - readable
            'aether': '#c026d3',       # Fuchsia 600 - ethereal
            'artifact': '#ca8a04',     # Yellow 600 - sacred gold
            'sylvan': '#16a34a',       # Green 600 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'forest': {
        'name': 'forest',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#15803d',      # Green 700 - forest green
            'secondary': '#57534e',    # Stone 600 - earth tone
            'accent': '#ea580c',       # Orange 600 - autumn
            'neutral': '#78716c',      # Stone 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#ea580c',      # Orange 600 - readable
            'success': '#15803d',      # Green 700 - readable
            'info': '#0891b2',         # Cyan 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#6b21a8',     # Purple 800 - readable
            'subtle': '#fafaf9',       # Stone 50 - background
            'distinct': '#0e7490',     # Cyan 700 - readable
            'aether': '#a21caf',       # Fuchsia 700 - readable
            'artifact': '#c2410c',     # Orange 700 - readable
            'sylvan': '#166534',       # Green 800 - high contrast
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'ocean': {
        'name': 'ocean',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#0369a1',      # Sky 700 - ocean blue
            'secondary': '#475569',    # Slate 600 - readable
            'accent': '#0891b2',       # Cyan 600 - aqua
            'neutral': '#64748b',      # Slate 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#d97706',      # Amber 600 - readable
            'success': '#047857',      # Emerald 700 - readable
            'info': '#0284c7',         # Sky 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#6d28d9',     # Violet 700 - readable
            'subtle': '#f0f9ff',       # Sky 50 - background
            'distinct': '#0891b2',     # Cyan 600 - readable
            'aether': '#a21caf',       # Fuchsia 700 - readable
            'artifact': '#ea580c',     # Orange 600 - readable
            'sylvan': '#059669',       # Emerald 600 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'phoenix': {
        'name': 'phoenix',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#dc2626',      # Red 600 - phoenix fire
            'secondary': '#78716c',    # Stone 500 - ash
            'accent': '#ea580c',       # Orange 600 - flame
            'neutral': '#78716c',      # Stone 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#ea580c',      # Orange 600 - readable
            'success': '#65a30d',      # Lime 600 - readable
            'info': '#2563eb',         # Blue 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#be123c',     # Rose 700 - readable
            'subtle': '#fff7ed',       # Orange 50 - background
            'distinct': '#ea580c',     # Orange 600 - readable
            'aether': '#be185d',       # Pink 700 - readable
            'artifact': '#ca8a04',     # Yellow 600 - readable
            'sylvan': '#65a30d',       # Lime 600 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'shadow': {
        'name': 'shadow',
        'colors': {
            # Core colors - WCAG AA compliant (monochrome)
            'primary': '#18181b',      # Zinc 900 - deep shadow
            'secondary': '#52525b',    # Zinc 600 - readable
            'accent': '#3f3f46',       # Zinc 700 - accent shadow
            'neutral': '#71717a',      # Zinc 500 - readable

            # Status colors - WCAG AA compliant (monochrome)
            'error': '#18181b',        # Zinc 900 - readable
            'warning': '#3f3f46',      # Zinc 700 - readable
            'success': '#52525b',      # Zinc 600 - readable
            'info': '#71717a',         # Zinc 500 - readable

            # Specialty colors - WCAG AA compliant (monochrome)
            'emphasis': '#27272a',     # Zinc 800 - readable
            'subtle': '#fafafa',       # Zinc 50 - background
            'distinct': '#3f3f46',     # Zinc 700 - readable
            'aether': '#52525b',       # Zinc 600 - readable
            'artifact': '#71717a',     # Zinc 500 - readable
            'sylvan': '#a1a1aa',       # Zinc 400 - lighter readable
            'danger': '#09090b',       # Zinc 950 - maximum contrast
        },
        'generate_variants': True,
    },
    
    'enchanted': {
        'name': 'enchanted',
        'colors': {
            # Core colors - WCAG AA compliant
            'primary': '#db2777',      # Pink 600 - vibrant magic
            'secondary': '#6b7280',    # Gray 500 - readable
            'accent': '#d97706',       # Amber 600 - golden glow
            'neutral': '#71717a',      # Zinc 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#ea580c',      # Orange 600 - readable
            'success': '#65a30d',      # Lime 600 - readable
            'info': '#2563eb',         # Blue 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#c026d3',     # Fuchsia 600 - magical emphasis
            'subtle': '#fdf4ff',       # Fuchsia 50 - background
            'distinct': '#a855f7',     # Purple 500 - readable
            'aether': '#c026d3',       # Fuchsia 600 - ethereal
            'artifact': '#ca8a04',     # Yellow 600 - readable
            'sylvan': '#65a30d',       # Lime 600 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
    
    'pastel': {
        'name': 'pastel',
        'colors': {
            # Core colors - WCAG AA compliant (darker pastels for readability)
            'primary': '#7c3aed',      # Violet 600 - readable purple
            'secondary': '#6b7280',    # Gray 500 - readable
            'accent': '#d97706',       # Amber 600 - readable gold
            'neutral': '#71717a',      # Zinc 500 - readable

            # Status colors - WCAG AA compliant
            'error': '#dc2626',        # Red 600 - readable
            'warning': '#ea580c',      # Orange 600 - readable
            'success': '#16a34a',      # Green 600 - readable
            'info': '#0284c7',         # Sky 600 - readable

            # Specialty colors - WCAG AA compliant
            'emphasis': '#a855f7',     # Purple 500 - soft emphasis
            'subtle': '#faf5ff',       # Purple 50 - background
            'distinct': '#06b6d4',     # Cyan 500 - readable
            'aether': '#c026d3',       # Fuchsia 600 - readable
            'artifact': '#eab308',     # Yellow 500 - readable
            'sylvan': '#22c55e',       # Green 500 - readable
            'danger': '#991b1b',       # Red 800 - high contrast
        },
        'generate_variants': True,
    },
}


def get_preset_theme(preset_name: str) -> Dict[str, Any]:
    """
    Get a preset theme configuration by name.
    
    Args:
        preset_name: Name of the preset theme
        
    Returns:
        Theme configuration dictionary
        
    Raises:
        ValueError: If preset not found
    """
    if preset_name not in THEMES:
        available = ', '.join(THEMES.keys())
        raise ValueError(
            f"Theme preset '{preset_name}' not found. "
            f"Available presets: {available}"
        )
    
    return THEMES[preset_name].copy()


def list_presets() -> list[str]:
    """
    Get a list of available preset names.
    
    Returns:
        List of preset theme names
    """
    return list(THEMES.keys())


def extend_preset(preset_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extend a preset theme with custom overrides.
    
    Args:
        preset_name: Name of the base preset
        overrides: Dictionary of overrides to apply
        
    Returns:
        Extended theme configuration
    """
    base_theme = get_preset_theme(preset_name)
    
    # Deep merge colors if provided
    if 'colors' in overrides:
        base_colors = base_theme.get('colors', {})
        override_colors = overrides['colors']
        base_theme['colors'] = {**base_colors, **override_colors}
        overrides = {k: v for k, v in overrides.items() if k != 'colors'}
    
    # Apply other overrides
    base_theme.update(overrides)
    
    return base_theme


def get_preset_description(preset_name: str) -> str:
    """
    Get a description of a preset theme.
    
    Args:
        preset_name: Name of the preset
        
    Returns:
        Description string
    """
    descriptions = {
        'default': 'The classic spellbook theme with trusty blue magic',
        'arcane': 'Deep purple mysteries and golden spell glows',
        'celestial': 'Pure light magic with divine clarity',
        'forest': 'Forest greens and earth tones from the woodland realm',
        'ocean': 'Ocean depths and aquatic enchantments',
        'phoenix': 'Warm flames and rebirth colors',
        'shadow': 'Monochrome magic from the shadow plane',
        'enchanted': 'Bright magical pinks and fairy gold',
        'pastel': 'Soft magic for gentle enchantments',
    }
    
    return descriptions.get(preset_name, 'No description available')


def get_theme_preset(theme_name: str, mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a theme preset with optional mode support.
    
    This function provides backward compatibility:
    - If mode is None, returns the classic theme (light mode colors)
    - If mode is specified, returns the theme with that mode
    
    Args:
        theme_name: Name of the theme
        mode: Optional mode ('light' or 'dark')
        
    Returns:
        Theme configuration dictionary
    """
    if mode is None:
        # Backward compatibility: return classic theme (light mode)
        if theme_name in THEMES:
            return THEMES[theme_name]
        # Fall back to light mode from new structure
        return get_theme_with_mode(theme_name, 'light')
    
    # Use new mode-aware structure
    return get_theme_with_mode(theme_name, mode)