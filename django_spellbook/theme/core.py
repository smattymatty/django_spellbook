"""
Core theme classes and data structures for Django Spellbook's theme system.
"""

from typing import Dict, Optional, Any
from .validator import validate_color


class ThemeColor:
    """Represents a single theme color with optional opacity variants."""
    
    def __init__(self, name: str, value: str, generate_variants: bool = True):
        """
        Initialize a ThemeColor.
        
        Args:
            name: The color name (e.g., 'primary', 'secondary')
            value: The color value (hex, rgb, or CSS color name)
            generate_variants: Whether to generate opacity variants
        """
        self.name = name
        self.value = validate_color(value)
        self.generate_variants = generate_variants
        self.variants = self._generate_variants() if generate_variants else {}
    
    def _generate_variants(self) -> Dict[str, str]:
        """Generate opacity variants for the color."""
        return {
            '25': f'color-mix(in srgb, {self.value} 25%, transparent)',
            '50': f'color-mix(in srgb, {self.value} 50%, transparent)',
            '75': f'color-mix(in srgb, {self.value} 75%, transparent)',
        }
    
    def to_css_var(self) -> str:
        """Convert to CSS variable name."""
        return f'--{self.name}-color'
    
    def to_css_declarations(self) -> Dict[str, str]:
        """
        Generate all CSS variable declarations for this color.
        
        Returns:
            Dictionary of CSS variable names to values
        """
        declarations = {self.to_css_var(): self.value}
        
        # Add variant declarations if enabled
        if self.generate_variants:
            for opacity, mix_value in self.variants.items():
                var_name = f'--{self.name}-color-{opacity}'
                declarations[var_name] = mix_value
        
        return declarations


class SpellbookTheme:
    """Main theme class that manages all color configurations."""
    
    # Default colors that match current CSS
    DEFAULT_COLORS = {
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
        # System colors for light mode (default)
        'background': '#ffffff',
        'surface': '#f9fafb',
        'text': '#1f2937',
        'text-secondary': '#6b7280',
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, mode: Optional[str] = None):
        """
        Initialize a SpellbookTheme.
        
        Args:
            config: Theme configuration dictionary from Django settings
            mode: Optional mode ('light' or 'dark')
        """
        self.config = config or {}
        self.name = self.config.get('name', 'default')
        self.mode = mode or 'light'
        self.generate_variants = self.config.get('generate_variants', True)
        self.colors = self._load_colors()
    
    def _load_colors(self) -> Dict[str, ThemeColor]:
        """
        Load and merge colors from configuration with defaults.
        
        Returns:
            Dictionary of color name to ThemeColor objects
        """
        # Start with default colors
        colors = {}
        
        # Merge defaults with user-provided colors
        merged_colors = self.DEFAULT_COLORS.copy()
        
        # Update with user colors if provided
        if 'colors' in self.config:
            merged_colors.update(self.config['colors'])
        
        # Add custom colors if provided
        if 'custom_colors' in self.config:
            merged_colors.update(self.config['custom_colors'])
        
        # Create ThemeColor objects
        for name, value in merged_colors.items():
            colors[name] = ThemeColor(name, value, self.generate_variants)
        
        return colors
    
    def get_color(self, name: str) -> Optional[ThemeColor]:
        """
        Get a specific color by name.
        
        Args:
            name: The color name
            
        Returns:
            ThemeColor object or None if not found
        """
        return self.colors.get(name)
    
    def to_css_declarations(self) -> Dict[str, str]:
        """
        Generate all CSS variable declarations for the theme.
        
        Returns:
            Dictionary of CSS variable names to values
        """
        declarations = {}
        
        for color in self.colors.values():
            declarations.update(color.to_css_declarations())
        
        return declarations
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert theme to a dictionary representation.
        
        Returns:
            Dictionary representation of the theme
        """
        return {
            'name': self.name,
            'colors': {name: color.value for name, color in self.colors.items()},
            'generate_variants': self.generate_variants,
        }
    
    @classmethod
    def from_preset(cls, preset_name: str) -> 'SpellbookTheme':
        """
        Create a theme from a preset.
        
        Args:
            preset_name: Name of the preset to use
            
        Returns:
            SpellbookTheme instance
            
        Raises:
            ValueError: If preset not found
        """
        from .presets import get_preset_theme
        preset_config = get_preset_theme(preset_name)
        return cls(preset_config)