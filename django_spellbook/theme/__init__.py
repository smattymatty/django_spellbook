"""
Django Spellbook Theme System

This module provides a Python-based color theming system for Django Spellbook,
allowing developers to configure colors through Django settings rather than
modifying CSS files directly.
"""

from .core import SpellbookTheme, ThemeColor
from .generator import generate_theme_css, generate_css_variables
from .validator import validate_color, is_valid_color
from .presets import THEMES, get_preset_theme, get_theme_preset
from .presets_with_modes import THEMES_WITH_MODES, get_theme_with_mode
from .modes import ThemeMode

__all__ = [
    'SpellbookTheme',
    'ThemeColor',
    'generate_theme_css',
    'generate_css_variables',
    'validate_color',
    'is_valid_color',
    'THEMES',
    'get_preset_theme',
    'get_theme_preset',
    'THEMES_WITH_MODES',
    'get_theme_with_mode',
    'ThemeMode',
]