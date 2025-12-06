"""Tests for dark mode alert color generation."""

import unittest
from django_spellbook.theme.generator import (
    _is_dark_color,
    _generate_dark_alert_variables,
    generate_css_variables
)


class TestDarkModeAlerts(unittest.TestCase):
    """Test alert color generation for dark mode."""
    
    def test_is_dark_color(self):
        """Test dark color detection."""
        # Dark colors
        self.assertTrue(_is_dark_color('#000000'))
        self.assertTrue(_is_dark_color('#1a1a1a'))
        self.assertTrue(_is_dark_color('#0d1117'))
        self.assertTrue(_is_dark_color('#1e293b'))
        
        # Light colors
        self.assertFalse(_is_dark_color('#ffffff'))
        self.assertFalse(_is_dark_color('#f9fafb'))
        self.assertFalse(_is_dark_color('#e5e7eb'))
        
    def test_generate_dark_alert_variables(self):
        """Test generation of dark mode alert variables."""
        declarations = {
            '--background-color': '#1a1a1a',
            '--info-color': '#2563eb',
            '--success-color': '#16a34a',
            '--warning-color': '#f59e0b',
            '--error-color': '#dc2626',
            '--primary-color': '#3b82f6',
            '--secondary-color': '#6b7280',
        }
        
        alert_vars = _generate_dark_alert_variables(declarations)
        
        # Check that all alert types have variables
        for alert_type in ['info', 'success', 'warning', 'error', 'danger', 'primary', 'secondary']:
            self.assertIn(f'--alert-{alert_type}-bg', alert_vars)
            self.assertIn(f'--alert-{alert_type}-border', alert_vars)
            self.assertIn(f'--alert-{alert_type}-text', alert_vars)
        
        # Check that colors mix with dark background
        self.assertIn('#1a1a1a', alert_vars['--alert-info-bg'])
        self.assertIn('20%', alert_vars['--alert-info-bg'])
        self.assertIn('40%', alert_vars['--alert-info-border'])
        self.assertIn('90%', alert_vars['--alert-info-text'])
        
    def test_css_variables_with_dark_theme(self):
        """Test that dark theme generates alert variables."""
        # Use a dark theme preset
        dark_theme_config = {
            'colors': {
                'background': '#0d1117',
                'surface': '#161b22',
                'text': '#e6edf3',
                'text-secondary': '#8b949e',
                'primary': '#58a6ff',
                'secondary': '#8b949e',
                'accent': '#f85149',
                'neutral': '#30363d',
                'success': '#56d364',
                'warning': '#e3b341',
                'error': '#f85149',
                'info': '#58a6ff',
            }
        }
        
        css = generate_css_variables(dark_theme_config)
        
        # Check that alert variables are present
        self.assertIn('--alert-info-bg:', css)
        self.assertIn('--alert-success-bg:', css)
        self.assertIn('--alert-warning-bg:', css)
        self.assertIn('--alert-error-bg:', css)
        
        # Check that they use the dark background (case-insensitive)
        self.assertIn('#0D1117', css.upper())
        
    def test_css_variables_with_light_theme(self):
        """Test that light theme doesn't generate alert variables."""
        # Use a light theme preset
        light_theme_config = {
            'colors': {
                'background': '#ffffff',
                'surface': '#f9fafb',
                'text': '#1f2937',
                'text-secondary': '#6b7280',
                'primary': '#3b82f6',
                'secondary': '#6b7280',
                'accent': '#f59e0b',
                'neutral': '#9ca3af',
                'success': '#16a34a',
                'warning': '#f59e0b',
                'error': '#dc2626',
                'info': '#2563eb',
            }
        }
        
        css = generate_css_variables(light_theme_config)
        
        # Check that alert variables are NOT present (use defaults)
        self.assertNotIn('--alert-info-bg:', css)
        self.assertNotIn('--alert-success-bg:', css)
        self.assertNotIn('--alert-warning-bg:', css)
        self.assertNotIn('--alert-error-bg:', css)


if __name__ == '__main__':
    unittest.main()