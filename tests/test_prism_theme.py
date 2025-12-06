"""Tests for Prism.js theme generation."""

import unittest
from django_spellbook.theme.generator import _generate_prism_variables, generate_css_variables


class TestPrismTheme(unittest.TestCase):
    """Test Prism.js theme CSS variable generation."""
    
    def test_generate_prism_variables_light_mode(self):
        """Test Prism variables in light mode."""
        declarations = {
            '--surface-color': '#f9fafb',
            '--background-color': '#ffffff',
            '--text-color': '#1f2937',
            '--text-secondary-color': '#6b7280',
            '--primary-color': '#3b82f6',
            '--secondary-color': '#6b7280',
            '--accent-color': '#f59e0b',
            '--success-color': '#16a34a',
            '--warning-color': '#f59e0b',
            '--error-color': '#dc2626',
            '--info-color': '#2563eb',
            '--neutral-color': '#9ca3af',
            '--emphasis-color': '#8b5cf6',
        }
        
        prism_vars = _generate_prism_variables(declarations, is_dark_mode=False)
        
        # Check that all essential Prism variables are present
        self.assertIn('--prism-text', prism_vars)
        self.assertIn('--prism-code-bg', prism_vars)
        self.assertIn('--prism-keyword', prism_vars)
        self.assertIn('--prism-string', prism_vars)
        self.assertIn('--prism-comment', prism_vars)
        self.assertIn('--prism-function', prism_vars)
        self.assertIn('--prism-number', prism_vars)
        self.assertIn('--prism-operator', prism_vars)
        
        # Check light mode specific values
        self.assertEqual(prism_vars['--prism-keyword'], '#3b82f6')  # Direct primary color
        self.assertEqual(prism_vars['--prism-text'], '#1f2937')
        
    def test_generate_prism_variables_dark_mode(self):
        """Test Prism variables in dark mode."""
        declarations = {
            '--surface-color': '#1a1a1a',
            '--background-color': '#0d1117',
            '--text-color': '#e6edf3',
            '--text-secondary-color': '#8b949e',
            '--primary-color': '#58a6ff',
            '--secondary-color': '#8b949e',
            '--accent-color': '#f85149',
            '--success-color': '#56d364',
            '--warning-color': '#e3b341',
            '--error-color': '#f85149',
            '--info-color': '#58a6ff',
            '--neutral-color': '#30363d',
            '--emphasis-color': '#d2a8ff',
        }
        
        prism_vars = _generate_prism_variables(declarations, is_dark_mode=True)
        
        # Check that all essential Prism variables are present
        self.assertIn('--prism-text', prism_vars)
        self.assertIn('--prism-code-bg', prism_vars)
        self.assertIn('--prism-keyword', prism_vars)
        self.assertIn('--prism-string', prism_vars)
        
        # Check dark mode specific values
        self.assertIn('80%', prism_vars['--prism-keyword'])  # Brightened for dark mode
        self.assertEqual(prism_vars['--prism-text'], '#e6edf3')
        
        # Check shadow is stronger in dark mode
        self.assertIn('40%', prism_vars['--prism-shadow'])
        
    def test_prism_ui_elements(self):
        """Test Prism UI element variables."""
        declarations = {
            '--primary-color': '#3b82f6',
            '--neutral-color': '#9ca3af',
            '--text-secondary-color': '#6b7280',
        }
        
        prism_vars = _generate_prism_variables(declarations, is_dark_mode=False)
        
        # Check toolbar and UI elements
        self.assertIn('--prism-toolbar-button-bg', prism_vars)
        self.assertIn('--prism-toolbar-button-hover', prism_vars)
        self.assertIn('--prism-language-label', prism_vars)
        self.assertIn('--prism-scrollbar-track', prism_vars)
        self.assertIn('--prism-scrollbar-thumb', prism_vars)
        
        # Check values
        self.assertEqual(prism_vars['--prism-toolbar-button-bg'], '#3b82f6')
        
    def test_css_variables_includes_prism(self):
        """Test that full CSS generation includes Prism variables."""
        # Dark theme config
        dark_theme_config = {
            'colors': {
                'background': '#0d1117',
                'surface': '#161b22',
                'text': '#e6edf3',
                'primary': '#58a6ff',
                'success': '#56d364',
            }
        }
        
        css = generate_css_variables(dark_theme_config)
        
        # Check that Prism variables are present
        self.assertIn('--prism-text:', css)
        self.assertIn('--prism-code-bg:', css)
        self.assertIn('--prism-keyword:', css)
        self.assertIn('--prism-string:', css)
        self.assertIn('--prism-comment:', css)
        self.assertIn('--prism-toolbar-button-bg:', css)
        
    def test_prism_diff_colors(self):
        """Test Prism diff highlighting colors."""
        declarations = {
            '--success-color': '#16a34a',
            '--error-color': '#dc2626',
        }
        
        prism_vars = _generate_prism_variables(declarations, is_dark_mode=False)
        
        # Check diff colors
        self.assertIn('--prism-inserted', prism_vars)
        self.assertIn('--prism-inserted-bg', prism_vars)
        self.assertIn('--prism-deleted', prism_vars)
        self.assertIn('--prism-deleted-bg', prism_vars)
        
        # Check values
        self.assertEqual(prism_vars['--prism-inserted'], '#16a34a')
        self.assertEqual(prism_vars['--prism-deleted'], '#dc2626')


if __name__ == '__main__':
    unittest.main()