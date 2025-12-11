"""
Tests for Django Spellbook's theme system.
"""

import unittest
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django_spellbook.theme import (
    SpellbookTheme,
    ThemeColor,
    generate_theme_css,
    generate_css_variables,
    validate_color,
    is_valid_color,
    THEMES,
    get_preset_theme,
)
from django_spellbook.theme.validator import (
    is_valid_hex_color,
    is_valid_rgb_color,
    is_valid_rgba_color,
    is_valid_css_color,
    normalize_hex_color,
    get_color_type,
)
from django_spellbook.theme.presets import (
    list_presets,
    extend_preset,
    get_preset_description,
)


class TestColorValidation(TestCase):
    """Test color validation functions."""
    
    def test_valid_hex_colors(self):
        """Test validation of hex color formats."""
        # Valid hex colors
        self.assertTrue(is_valid_hex_color('#fff'))
        self.assertTrue(is_valid_hex_color('#FFF'))
        self.assertTrue(is_valid_hex_color('#ffffff'))
        self.assertTrue(is_valid_hex_color('#FFFFFF'))
        self.assertTrue(is_valid_hex_color('#123456'))
        self.assertTrue(is_valid_hex_color('#abcdef'))
        
        # Invalid hex colors
        self.assertFalse(is_valid_hex_color('fff'))
        self.assertFalse(is_valid_hex_color('#ff'))
        self.assertFalse(is_valid_hex_color('#ffff'))
        self.assertFalse(is_valid_hex_color('#gggggg'))
        self.assertFalse(is_valid_hex_color(''))
    
    def test_valid_rgb_colors(self):
        """Test validation of RGB color formats."""
        # Valid RGB colors
        self.assertTrue(is_valid_rgb_color('rgb(0, 0, 0)'))
        self.assertTrue(is_valid_rgb_color('rgb(255, 255, 255)'))
        self.assertTrue(is_valid_rgb_color('rgb(123, 45, 67)'))
        self.assertTrue(is_valid_rgb_color('rgb( 100 , 100 , 100 )'))
        
        # Invalid RGB colors
        self.assertFalse(is_valid_rgb_color('rgb(256, 0, 0)'))
        self.assertFalse(is_valid_rgb_color('rgb(-1, 0, 0)'))
        self.assertFalse(is_valid_rgb_color('rgb(0, 0)'))
        self.assertFalse(is_valid_rgb_color('rgba(0, 0, 0)'))
        self.assertFalse(is_valid_rgb_color(''))
    
    def test_valid_rgba_colors(self):
        """Test validation of RGBA color formats."""
        # Valid RGBA colors
        self.assertTrue(is_valid_rgba_color('rgba(0, 0, 0, 0)'))
        self.assertTrue(is_valid_rgba_color('rgba(255, 255, 255, 1)'))
        self.assertTrue(is_valid_rgba_color('rgba(123, 45, 67, 0.5)'))
        self.assertTrue(is_valid_rgba_color('rgba( 100 , 100 , 100 , .75 )'))
        
        # Invalid RGBA colors
        self.assertFalse(is_valid_rgba_color('rgba(256, 0, 0, 0)'))
        self.assertFalse(is_valid_rgba_color('rgba(0, 0, 0, 1.5)'))
        self.assertFalse(is_valid_rgba_color('rgba(0, 0, 0, -0.5)'))
        self.assertFalse(is_valid_rgba_color('rgb(0, 0, 0)'))
        self.assertFalse(is_valid_rgba_color(''))
    
    def test_valid_css_colors(self):
        """Test validation of CSS named colors."""
        # Valid CSS colors
        self.assertTrue(is_valid_css_color('red'))
        self.assertTrue(is_valid_css_color('RED'))
        self.assertTrue(is_valid_css_color('Blue'))
        self.assertTrue(is_valid_css_color('transparent'))
        self.assertTrue(is_valid_css_color('darkslateblue'))
        
        # Invalid CSS colors
        self.assertFalse(is_valid_css_color('notacolor'))
        self.assertFalse(is_valid_css_color('#ffffff'))
        self.assertFalse(is_valid_css_color(''))
    
    def test_normalize_hex_color(self):
        """Test hex color normalization."""
        self.assertEqual(normalize_hex_color('#fff'), '#FFFFFF')
        self.assertEqual(normalize_hex_color('#FFF'), '#FFFFFF')
        self.assertEqual(normalize_hex_color('#abc'), '#AABBCC')
        self.assertEqual(normalize_hex_color('#123456'), '#123456')
        self.assertEqual(normalize_hex_color('#abcdef'), '#ABCDEF')
        
        # Should raise error for invalid hex
        with self.assertRaises(ValueError):
            normalize_hex_color('not-a-hex')
    
    def test_validate_color(self):
        """Test comprehensive color validation."""
        # Valid colors should be returned (normalized if hex)
        self.assertEqual(validate_color('#fff'), '#FFFFFF')
        self.assertEqual(validate_color('rgb(0, 0, 0)'), 'rgb(0, 0, 0)')
        self.assertEqual(validate_color('rgba(0, 0, 0, 0.5)'), 'rgba(0, 0, 0, 0.5)')
        self.assertEqual(validate_color('red'), 'red')
        self.assertEqual(validate_color('RED'), 'red')
        
        # Invalid colors should raise ValueError
        with self.assertRaises(ValueError):
            validate_color('')
        with self.assertRaises(ValueError):
            validate_color('not-a-color')
        with self.assertRaises(ValueError):
            validate_color('#gg')
    
    def test_get_color_type(self):
        """Test color type detection."""
        self.assertEqual(get_color_type('#fff'), 'hex')
        self.assertEqual(get_color_type('rgb(0, 0, 0)'), 'rgb')
        self.assertEqual(get_color_type('rgba(0, 0, 0, 0)'), 'rgba')
        self.assertEqual(get_color_type('red'), 'css')
        self.assertIsNone(get_color_type('not-a-color'))
        self.assertIsNone(get_color_type(''))


class TestThemeColor(TestCase):
    """Test ThemeColor class."""
    
    def test_theme_color_creation(self):
        """Test creating a ThemeColor instance."""
        color = ThemeColor('primary', '#3b82f6')
        self.assertEqual(color.name, 'primary')
        self.assertEqual(color.value, '#3B82F6')  # Normalized
        self.assertTrue(color.generate_variants)
        self.assertIn('25', color.variants)
        self.assertIn('50', color.variants)
        self.assertIn('75', color.variants)
    
    def test_theme_color_no_variants(self):
        """Test creating a ThemeColor without variants."""
        color = ThemeColor('primary', '#3b82f6', generate_variants=False)
        self.assertEqual(color.name, 'primary')
        self.assertEqual(color.value, '#3B82F6')
        self.assertFalse(color.generate_variants)
        self.assertEqual(color.variants, {})
    
    def test_theme_color_css_var(self):
        """Test CSS variable name generation."""
        color = ThemeColor('primary', '#3b82f6')
        self.assertEqual(color.to_css_var(), '--primary-color')
    
    def test_theme_color_css_declarations(self):
        """Test CSS declarations generation."""
        color = ThemeColor('primary', '#3b82f6')
        declarations = color.to_css_declarations()
        
        self.assertEqual(declarations['--primary-color'], '#3B82F6')
        self.assertIn('--primary-color-25', declarations)
        self.assertIn('--primary-color-50', declarations)
        self.assertIn('--primary-color-75', declarations)
        
        # Check that variants use color-mix
        self.assertIn('color-mix', declarations['--primary-color-25'])


class TestSpellbookTheme(TestCase):
    """Test SpellbookTheme class."""
    
    def test_default_theme(self):
        """Test creating a theme with defaults."""
        theme = SpellbookTheme()
        
        self.assertEqual(theme.name, 'default')
        self.assertTrue(theme.generate_variants)
        self.assertIn('primary', theme.colors)
        self.assertIn('secondary', theme.colors)
        
        # Check default color values
        primary = theme.get_color('primary')
        self.assertEqual(primary.value, '#3B82F6')
    
    def test_custom_theme(self):
        """Test creating a theme with custom configuration."""
        config = {
            'name': 'custom',
            'colors': {
                'primary': '#ff0000',
                'secondary': '#00ff00',
            },
            'generate_variants': False,
        }
        
        theme = SpellbookTheme(config)
        
        self.assertEqual(theme.name, 'custom')
        self.assertFalse(theme.generate_variants)
        
        # Custom colors should override defaults
        primary = theme.get_color('primary')
        self.assertEqual(primary.value, '#FF0000')
        
        # Other defaults should still be present
        self.assertIn('accent', theme.colors)
    
    def test_custom_colors_addition(self):
        """Test adding custom colors to theme."""
        config = {
            'custom_colors': {
                'brand': '#ff6600',
                'highlight': '#00ff00',
            }
        }
        
        theme = SpellbookTheme(config)
        
        # Custom colors should be added
        brand = theme.get_color('brand')
        self.assertIsNotNone(brand)
        self.assertEqual(brand.value, '#FF6600')
        
        # Defaults should still be present
        self.assertIn('primary', theme.colors)
    
    def test_theme_to_dict(self):
        """Test converting theme to dictionary."""
        config = {
            'name': 'test',
            'colors': {
                'primary': '#123456',
            }
        }
        
        theme = SpellbookTheme(config)
        theme_dict = theme.to_dict()
        
        self.assertEqual(theme_dict['name'], 'test')
        self.assertEqual(theme_dict['colors']['primary'], '#123456')
        self.assertTrue(theme_dict['generate_variants'])
    
    def test_theme_from_preset(self):
        """Test creating theme from preset."""
        theme = SpellbookTheme.from_preset('arcane')
        
        self.assertEqual(theme.name, 'arcane')
        self.assertIn('primary', theme.colors)

        # Should have arcane colors (updated for WCAG AA compliance)
        primary = theme.get_color('primary')
        self.assertEqual(primary.value, '#7C3AED')


class TestCSSGeneration(TestCase):
    """Test CSS generation functions."""
    
    def test_generate_css_variables_default(self):
        """Test generating CSS variables with default theme."""
        css = generate_css_variables()
        
        self.assertIn(':root {', css)
        self.assertIn('--primary-color:', css)
        self.assertIn('--secondary-color:', css)
        self.assertIn('#3B82F6', css)  # Default primary color
    
    def test_generate_css_variables_custom(self):
        """Test generating CSS variables with custom theme."""
        config = {
            'colors': {
                'primary': '#ff0000',
            }
        }
        
        css = generate_css_variables(config)
        
        self.assertIn(':root {', css)
        self.assertIn('--primary-color: #FF0000;', css)
    
    def test_generate_theme_css(self):
        """Test complete theme CSS generation."""
        config = {
            'colors': {
                'primary': '#123456',
            }
        }
        
        css = generate_theme_css(config)
        
        self.assertIn(':root {', css)
        self.assertIn('--primary-color: #123456;', css)
        
        # Should include opacity variants
        self.assertIn('--primary-color-25:', css)
        self.assertIn('color-mix', css)


class TestThemePresets(TestCase):
    """Test theme preset functions."""
    
    def test_get_preset_theme(self):
        """Test getting a preset theme."""
        preset = get_preset_theme('arcane')

        self.assertEqual(preset['name'], 'arcane')
        self.assertIn('colors', preset)
        # Updated for WCAG AA compliance
        self.assertEqual(preset['colors']['primary'], '#7c3aed')
    
    def test_get_invalid_preset(self):
        """Test getting an invalid preset."""
        with self.assertRaises(ValueError) as cm:
            get_preset_theme('not_a_preset')
        
        self.assertIn('not found', str(cm.exception))
        self.assertIn('Available presets', str(cm.exception))
    
    def test_list_presets(self):
        """Test listing available presets."""
        presets = list_presets()
        
        self.assertIn('default', presets)
        self.assertIn('arcane', presets)
        self.assertIn('ocean', presets)
        self.assertIn('forest', presets)
    
    def test_extend_preset(self):
        """Test extending a preset with overrides."""
        extended = extend_preset('default', {
            'colors': {
                'primary': '#ff0000',
            },
            'name': 'custom_extended',
        })
        
        self.assertEqual(extended['name'], 'custom_extended')
        self.assertEqual(extended['colors']['primary'], '#ff0000')
        # Should keep other default colors
        self.assertIn('secondary', extended['colors'])
    
    def test_get_preset_description(self):
        """Test getting preset descriptions."""
        desc = get_preset_description('arcane')
        self.assertIn('purple', desc.lower())
        
        desc = get_preset_description('not_a_preset')
        self.assertEqual(desc, 'No description available')


class TestTemplateTag(TestCase):
    """Test the spellbook_styles template tag."""
    
    @override_settings(SPELLBOOK_THEME=None)
    def test_spellbook_styles_default(self):
        """Test spellbook_styles tag with no configuration."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        result = spellbook_styles()
        
        # Should return context dictionary with theme_css
        self.assertIsInstance(result, dict)
        self.assertIn('theme_css', result)
        
        # Theme CSS should contain default variables
        theme_css = result['theme_css']
        self.assertIn(':root {', theme_css)
        self.assertIn('--primary-color:', theme_css)
        self.assertIn('#3B82F6', theme_css)  # Default primary color
    
    @override_settings(SPELLBOOK_THEME={'colors': {'primary': '#ff0000'}})
    def test_spellbook_styles_custom(self):
        """Test spellbook_styles tag with custom configuration."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        result = spellbook_styles()
        
        # Should return context dictionary with theme_css
        self.assertIsInstance(result, dict)
        self.assertIn('theme_css', result)
        
        # Should include custom color
        theme_css = result['theme_css']
        self.assertIn('--primary-color: #FF0000;', theme_css)