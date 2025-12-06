"""Tests for card CSS variable generation."""

import unittest
from django_spellbook.theme.generator import _generate_card_variables, generate_css_variables


class TestCardVariables(unittest.TestCase):
    """Test card CSS variable generation."""
    
    def test_generate_card_variables_light_mode(self):
        """Test card variables in light mode."""
        declarations = {
            '--surface-color': '#f9fafb',
            '--neutral-color': '#9ca3af',
            '--text-color': '#1f2937',
        }
        
        card_vars = _generate_card_variables(declarations, is_dark_mode=False)
        
        # Check that all card variables are present
        self.assertIn('--card-bg', card_vars)
        self.assertIn('--card-header-bg', card_vars)
        self.assertIn('--card-footer-bg', card_vars)
        self.assertIn('--card-border', card_vars)
        self.assertIn('--card-shadow', card_vars)
        self.assertIn('--card-title-color', card_vars)
        
        # Check light mode specific values
        self.assertEqual(card_vars['--card-bg'], '#f9fafb')
        self.assertIn('5%', card_vars['--card-header-bg'])  # Light mixing
        
    def test_generate_card_variables_dark_mode(self):
        """Test card variables in dark mode."""
        declarations = {
            '--surface-color': '#1a1a1a',
            '--neutral-color': '#30363d',
            '--text-color': '#e6edf3',
        }
        
        card_vars = _generate_card_variables(declarations, is_dark_mode=True)
        
        # Check that all card variables are present
        self.assertIn('--card-bg', card_vars)
        self.assertIn('--card-header-bg', card_vars)
        self.assertIn('--card-footer-bg', card_vars)
        self.assertIn('--card-border', card_vars)
        self.assertIn('--card-shadow', card_vars)
        self.assertIn('--card-title-color', card_vars)
        
        # Check dark mode specific values
        self.assertEqual(card_vars['--card-bg'], '#1a1a1a')
        self.assertIn('15%', card_vars['--card-header-bg'])  # Darker mixing
        self.assertIn('30%', card_vars['--card-shadow'])  # Stronger shadows
        
    def test_css_variables_includes_cards(self):
        """Test that full CSS generation includes card variables."""
        # Dark theme config
        dark_theme_config = {
            'colors': {
                'background': '#0d1117',
                'surface': '#161b22',
                'text': '#e6edf3',
                'neutral': '#30363d',
            }
        }
        
        css = generate_css_variables(dark_theme_config)
        
        # Check that card variables are present
        self.assertIn('--card-bg:', css)
        self.assertIn('--card-header-bg:', css)
        self.assertIn('--card-footer-bg:', css)
        self.assertIn('--card-border:', css)
        self.assertIn('--card-shadow:', css)
        
        # Light theme config
        light_theme_config = {
            'colors': {
                'background': '#ffffff',
                'surface': '#f9fafb',
                'text': '#1f2937',
                'neutral': '#9ca3af',
            }
        }
        
        css = generate_css_variables(light_theme_config)
        
        # Card variables should still be present in light mode
        self.assertIn('--card-bg:', css)
        self.assertIn('--card-header-bg:', css)


if __name__ == '__main__':
    unittest.main()