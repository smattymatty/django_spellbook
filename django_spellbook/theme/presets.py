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
            'primary': '#3b82f6',
            'secondary': '#6b7280',
            'accent': '#f59e0b',
            'neutral': '#2563eb',
            'error': '#dc2626',
            'warning': '#f59e0b',
            'success': '#16a34a',
            'info': '#2563eb',
            'emphasis': '#8b5cf6',
            'subtle': '#f3f4f6',
            'distinct': '#06b6d4',
            'aether': '#c026d3',
            'artifact': '#a16207',
            'sylvan': '#3f6212',
            'danger': '#a80000',
        },
        'generate_variants': True,
    },
    
    'arcane': {
        'name': 'arcane',
        'colors': {
            'primary': '#9D4EDD',      # Deep purple magic
            'secondary': '#240046',    # Midnight purple
            'accent': '#FFB700',       # Golden spell glow
            'neutral': '#3C096C',      # Dark mystic purple
            'error': '#D00000',        # Blood magic red
            'warning': '#FFAA00',      # Amber warning
            'success': '#7FB800',      # Nature spell green
            'info': '#7209B7',         # Arcane knowledge
            'emphasis': '#C77DFF',     # Light magic purple
            'subtle': '#10002B',       # Deep void
            'distinct': '#E0AAFF',     # Ethereal lavender
            'aether': '#F72585',       # Pink magical energy
            'artifact': '#FFD60A',     # Ancient gold
            'sylvan': '#55A630',       # Forest magic
            'danger': '#9D0208',       # Dark curse red
        },
        'generate_variants': True,
    },
    
    'celestial': {
        'name': 'celestial',
        'colors': {
            'primary': '#4CC9F0',      # Celestial blue
            'secondary': '#7209B7',    # Divine purple
            'accent': '#F7E60F',       # Holy light gold
            'neutral': '#CAD2C5',      # Cloud gray
            'error': '#F07167',        # Dawn red
            'warning': '#FFA62B',      # Sun warning
            'success': '#8FE1A2',      # Blessed green
            'info': '#4361EE',         # Heaven blue
            'emphasis': '#A663CC',     # Divine emphasis
            'subtle': '#F7F7FF',       # Pure white light
            'distinct': '#B4E7FC',     # Sky distinction
            'aether': '#E0AAFF',       # Ethereal purple
            'artifact': '#FFD23F',     # Sacred gold
            'sylvan': '#95D5B2',       # Heavenly garden
            'danger': '#D62828',       # Celestial wrath
        },
        'generate_variants': True,
    },
    
    'forest': {
        'name': 'forest',
        'colors': {
            'primary': '#2d5016',
            'secondary': '#3e2723',
            'accent': '#ff6f00',
            'neutral': '#5d4037',
            'error': '#b71c1c',
            'warning': '#ff6f00',
            'success': '#1b5e20',
            'info': '#004d40',
            'emphasis': '#4a148c',
            'subtle': '#efebe9',
            'distinct': '#006064',
            'aether': '#6a1b9a',
            'artifact': '#bf360c',
            'sylvan': '#33691e',
            'danger': '#880e4f',
        },
        'generate_variants': True,
    },
    
    'ocean': {
        'name': 'ocean',
        'colors': {
            'primary': '#006994',
            'secondary': '#01579b',
            'accent': '#00acc1',
            'neutral': '#455a64',
            'error': '#d32f2f',
            'warning': '#ffa000',
            'success': '#00796b',
            'info': '#0277bd',
            'emphasis': '#4527a0',
            'subtle': '#e0f7fa',
            'distinct': '#00bcd4',
            'aether': '#7b1fa2',
            'artifact': '#ff8f00',
            'sylvan': '#2e7d32',
            'danger': '#c62828',
        },
        'generate_variants': True,
    },
    
    'phoenix': {
        'name': 'phoenix',
        'colors': {
            'primary': '#ff6b35',
            'secondary': '#f77b71',
            'accent': '#ffc947',
            'neutral': '#a8716a',
            'error': '#c73e1d',
            'warning': '#ffc947',
            'success': '#5eb319',
            'info': '#4a90e2',
            'emphasis': '#b8336a',
            'subtle': '#fff5e6',
            'distinct': '#ff9a00',
            'aether': '#c9184a',
            'artifact': '#d4a574',
            'sylvan': '#7cb342',
            'danger': '#b71c1c',
        },
        'generate_variants': True,
    },
    
    'shadow': {
        'name': 'shadow',
        'colors': {
            'primary': '#000000',
            'secondary': '#333333',
            'accent': '#666666',
            'neutral': '#999999',
            'error': '#000000',
            'warning': '#333333',
            'success': '#666666',
            'info': '#999999',
            'emphasis': '#000000',
            'subtle': '#f5f5f5',
            'distinct': '#333333',
            'aether': '#666666',
            'artifact': '#999999',
            'sylvan': '#cccccc',
            'danger': '#000000',
        },
        'generate_variants': True,
    },
    
    'enchanted': {
        'name': 'enchanted',
        'colors': {
            'primary': '#FF006E',    
            'secondary': '#FB5607',    
            'accent': '#FFBE0B',       
            'neutral': '#8338EC',      
            'error': '#E01E37',        
            'warning': '#FF9500',      
            'success': '#95D600',      
            'info': '#3A86FF',         
            'emphasis': '#FF4CC4',     
            'subtle': '#FFE5F1',       
            'distinct': '#C77DFF',     
            'aether': '#FF10F0',       
            'artifact': '#FFD700',     
            'sylvan': '#7CB518',       
            'danger': '#DC2F02',       
        },
        'generate_variants': True,
    },
    
    'pastel': {
        'name': 'pastel',
        'colors': {
            'primary': '#b19cd9',
            'secondary': '#ffb6c1',
            'accent': '#ffd700',
            'neutral': '#e6e6fa',
            'error': '#ff91a4',
            'warning': '#ffcc99',
            'success': '#90ee90',
            'info': '#87ceeb',
            'emphasis': '#dda0dd',
            'subtle': '#faf0e6',
            'distinct': '#98fb98',
            'aether': '#ff99ff',
            'artifact': '#f0e68c',
            'sylvan': '#98d98e',
            'danger': '#ffb3ba',
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