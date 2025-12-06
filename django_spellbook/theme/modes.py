"""
Theme mode system for Django Spellbook.

Provides light/dark mode variants for all themes.
"""

from typing import Dict, Any, Optional


class ThemeMode:
    """Constants and utilities for theme modes."""
    
    LIGHT = 'light'
    DARK = 'dark'
    
    # Available modes
    MODES = [LIGHT, DARK]
    
    @classmethod
    def is_valid_mode(cls, mode: str) -> bool:
        """Check if a mode is valid."""
        return mode in cls.MODES
    
    @classmethod
    def get_default_mode(cls) -> str:
        """Get the default mode."""
        return cls.LIGHT


def adjust_color_for_dark_mode(color: str, adjustment_type: str = 'primary') -> str:
    """
    Adjust a color for dark mode.
    
    This is a helper for automatically generating dark mode colors.
    In practice, we'll manually define dark mode colors for better results.
    
    Args:
        color: The original color (hex, rgb, etc.)
        adjustment_type: Type of adjustment ('primary', 'background', 'text')
        
    Returns:
        Adjusted color for dark mode
    """
    # For now, return the original color
    # This will be enhanced with actual color manipulation if needed
    return color


def get_dark_mode_colors(light_colors: Dict[str, str]) -> Dict[str, str]:
    """
    Generate dark mode colors from light mode colors.
    
    This provides automatic dark mode generation as a fallback,
    but manually defined dark colors are preferred.
    
    Args:
        light_colors: Dictionary of light mode colors
        
    Returns:
        Dictionary of dark mode colors
    """
    dark_colors = {}
    
    # Define how each color type should be adjusted
    adjustments = {
        'background': '#0A0A0F',  # Very dark
        'surface': '#1A1A2E',      # Slightly lighter than background
        'text': '#F0F0F0',          # Light text
        'text-secondary': '#B8B8D0', # Slightly dimmed text
    }
    
    for key, value in light_colors.items():
        if key in adjustments:
            dark_colors[key] = adjustments[key]
        else:
            # For other colors, use the same value (will be manually overridden)
            dark_colors[key] = value
    
    return dark_colors