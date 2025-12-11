"""
Integration tests for Django Spellbook's theme system.
"""

from unittest.mock import patch
from django.test import TestCase, override_settings
from django.template import Template, Context


class TestThemeIntegration(TestCase):
    """Test theme system integration across components."""
    
    def test_default_theme_colors(self):
        """Test that default theme provides all required colors."""
        from django_spellbook.theme import SpellbookTheme
        
        # Create theme with no config (uses defaults)
        theme = SpellbookTheme()
        
        # Check all semantic colors have values
        self.assertIsNotNone(theme.get_color('primary'))
        self.assertIsNotNone(theme.get_color('secondary'))
        self.assertIsNotNone(theme.get_color('accent'))
        self.assertIsNotNone(theme.get_color('neutral'))
        self.assertIsNotNone(theme.get_color('success'))
        self.assertIsNotNone(theme.get_color('warning'))
        self.assertIsNotNone(theme.get_color('error'))
        self.assertIsNotNone(theme.get_color('info'))
        
        # Check CSS declarations are generated
        css_declarations = theme.to_css_declarations()
        self.assertIn('--primary-color', css_declarations)
        self.assertIn('--secondary-color', css_declarations)
        
        # Check opacity variants exist
        self.assertIn('--primary-color-25', css_declarations)
        self.assertIn('--primary-color-50', css_declarations)
        self.assertIn('--primary-color-75', css_declarations)
    
    @override_settings(SPELLBOOK_THEME={'colors': {'primary': '#123456'}})
    def test_custom_theme_from_settings(self):
        """Test that custom theme from settings is applied."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        # Generate styles with custom settings
        context = spellbook_styles()
        theme_css = context['theme_css']
        
        # Check custom color is applied
        self.assertIn('--primary-color: #123456;', theme_css)
        
        # Check other colors still have defaults
        self.assertIn('--secondary-color:', theme_css)
        self.assertIn('--accent-color:', theme_css)
    
    def test_preset_themes(self):
        """Test that all preset themes work correctly."""
        from django_spellbook.theme import THEMES, generate_theme_css
        
        expected_themes = [
            'default', 'arcane', 'celestial', 'forest', 
            'ocean', 'phoenix', 'shadow', 'enchanted', 'pastel'
        ]
        
        # Check all expected themes exist
        for theme_name in expected_themes:
            with self.subTest(theme=theme_name):
                self.assertIn(theme_name, THEMES)
                
                # Generate CSS for theme
                theme_config = THEMES[theme_name]
                css = generate_theme_css(theme_config)
                
                # Verify CSS is valid
                self.assertIn(':root {', css)
                self.assertIn('--primary-color:', css)
                self.assertIn('}', css)
                
                # Check CSS has actual color values (not empty)
                self.assertNotIn('--primary-color: ;', css)
                self.assertNotIn('--primary-color:;', css)
    
    def test_theme_css_in_template_context(self):
        """Test that theme CSS is properly passed to template context."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        # Get context from template tag
        context = spellbook_styles()
        
        # Check context structure
        self.assertIsInstance(context, dict)
        self.assertIn('theme_css', context)
        self.assertIsInstance(context['theme_css'], str)
        
        # Check CSS content
        theme_css = context['theme_css']
        self.assertTrue(theme_css.startswith(':root {'))
        self.assertTrue(theme_css.endswith('}'))
        self.assertGreater(len(theme_css), 100)  # Should have substantial content
    
    def test_theme_with_partial_config(self):
        """Test theme with partial configuration (some colors customized)."""
        from django_spellbook.theme import SpellbookTheme
        
        config = {
            'colors': {
                'primary': '#FF0000',
                'accent': 'rgb(0, 255, 0)'
            }
        }
        
        theme = SpellbookTheme(config)
        
        # Check customized colors
        self.assertEqual(theme.get_color('primary').value, '#FF0000')
        self.assertEqual(theme.get_color('accent').value, 'rgb(0, 255, 0)')
        
        # Check other colors have defaults
        self.assertIsNotNone(theme.get_color('secondary'))
        self.assertIsNotNone(theme.get_color('neutral'))
        self.assertNotEqual(theme.get_color('secondary').value, '')
    
    def test_theme_css_color_mix_syntax(self):
        """Test that opacity variants use correct color-mix syntax."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        context = spellbook_styles()
        theme_css = context['theme_css']
        
        # Check color-mix syntax for opacity variants
        self.assertIn('color-mix(in srgb,', theme_css)
        self.assertIn('25%, transparent)', theme_css)
        self.assertIn('50%, transparent)', theme_css)
        self.assertIn('75%, transparent)', theme_css)
    
    def test_preset_theme_by_name(self):
        """Test using preset theme by name string."""
        from django_spellbook.theme import THEMES, generate_theme_css
        
        # Get arcane theme config
        arcane_theme = THEMES['arcane']
        
        # Generate styles with arcane preset
        theme_css = generate_theme_css(arcane_theme)

        # Get expected primary color (updated for WCAG AA compliance)
        arcane_primary = arcane_theme['colors']['primary']

        # Check arcane theme colors are applied (uppercase for CSS)
        self.assertIn(f'--primary-color: {arcane_primary.upper()}', theme_css)
    
    def test_theme_css_complete_integration(self):
        """Test complete integration of theme CSS generation."""
        # Create a template that uses theme styles
        template_string = """
        {% load spellbook_tags %}
        {% spellbook_styles %}
        """
        
        template = Template(template_string)
        rendered = template.render(Context())
        
        # Check all components are present
        # 1. Theme CSS variables
        self.assertIn('<style id="spellbook-theme">', rendered)
        self.assertIn(':root {', rendered)
        self.assertIn('--primary-color:', rendered)
        
        # 2. CSS file links
        self.assertIn('colors.css', rendered)
        self.assertIn('utilities.css', rendered)
        self.assertIn('styles.css', rendered)
        
        # 3. Proper structure
        self.assertIn('</style>', rendered)
        self.assertIn('<link rel="stylesheet"', rendered)
    
    def test_invalid_theme_config_fallback(self):
        """Test that invalid theme config falls back to defaults."""
        from django_spellbook.theme import SpellbookTheme
        
        # Invalid configs that should raise ValueError
        invalid_configs = [
            {'colors': {'primary': 'not-a-color'}},
            {'colors': {'primary': '#GG0000'}},  # Invalid hex
            {'colors': {'primary': 'rgb(256, 0, 0)'}},  # Out of range
        ]
        
        for config in invalid_configs:
            with self.subTest(config=config):
                # Invalid colors should raise ValueError during validation
                with self.assertRaises(ValueError):
                    theme = SpellbookTheme(config)