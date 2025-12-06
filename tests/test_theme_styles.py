"""
Tests for Django Spellbook's theme styles and CSS loading.
"""

import os
from unittest.mock import patch, Mock
from django.test import TestCase
from django.template import Template, Context
from django.conf import settings


class TestColorUtilitiesLoading(TestCase):
    """Test that color utility CSS files are loaded correctly."""
    
    def test_colors_css_file_exists(self):
        """Test that colors.css file exists in the static directory."""
        # Get the package directory
        import django_spellbook
        package_dir = os.path.dirname(django_spellbook.__file__)
        colors_css_path = os.path.join(
            package_dir, 
            'static', 
            'django_spellbook', 
            'css_modules', 
            'utilities', 
            'colors.css'
        )
        
        # Check file exists
        self.assertTrue(
            os.path.exists(colors_css_path),
            f"colors.css not found at {colors_css_path}"
        )
        
        # Check file is not empty
        with open(colors_css_path, 'r') as f:
            content = f.read()
            self.assertGreater(len(content), 100, "colors.css appears to be empty")
            
            # Check for expected color utility classes
            self.assertIn('.sb-bg-primary', content)
            self.assertIn('.sb-bg-secondary', content)
            self.assertIn('.sb-bg-accent', content)
            self.assertIn('.sb-bg-success', content)
            self.assertIn('.sb-bg-warning', content)
            self.assertIn('.sb-bg-error', content)
            self.assertIn('.sb-bg-info', content)
            self.assertIn('.sb-bg-neutral', content)
    
    def test_spellbook_styles_template_includes_colors(self):
        """Test that spellbook_styles template includes colors.css link."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        # Get the template context
        context = spellbook_styles()
        
        # Load and render the template
        from django.template.loader import get_template
        template = get_template('django_spellbook/data/styles.html')
        rendered = template.render(context)
        
        # Check that colors.css is included
        self.assertIn('django_spellbook/css_modules/utilities/colors.css', rendered)
        self.assertIn('<link rel="stylesheet"', rendered)
        
        # Also check other required CSS files
        self.assertIn('django_spellbook/utilities.css', rendered)
        self.assertIn('django_spellbook/styles.css', rendered)
    
    def test_color_utility_classes_defined(self):
        """Test that color utility classes are properly defined with CSS variables."""
        import django_spellbook
        package_dir = os.path.dirname(django_spellbook.__file__)
        colors_css_path = os.path.join(
            package_dir, 
            'static', 
            'django_spellbook', 
            'css_modules', 
            'utilities', 
            'colors.css'
        )
        
        with open(colors_css_path, 'r') as f:
            content = f.read()
            
            # Test background color utilities use CSS variables
            self.assertIn('background-color: var(--primary-color', content)
            self.assertIn('background-color: var(--secondary-color', content)
            self.assertIn('background-color: var(--accent-color', content)
            
            # Test text color utilities
            self.assertIn('.sb-text-primary', content)
            self.assertIn('color: var(--primary-color', content)
            
            # Test opacity variants
            self.assertIn('.sb-bg-primary-25', content)
            self.assertIn('.sb-bg-primary-50', content)
            self.assertIn('.sb-bg-primary-75', content)
    
    def test_css_variables_generation(self):
        """Test that CSS variables are generated in the theme CSS."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        # Get the generated CSS
        context = spellbook_styles()
        theme_css = context['theme_css']
        
        # Check that CSS variables are defined
        self.assertIn(':root {', theme_css)
        self.assertIn('--primary-color:', theme_css)
        self.assertIn('--secondary-color:', theme_css)
        self.assertIn('--accent-color:', theme_css)
        self.assertIn('--neutral-color:', theme_css)
        self.assertIn('--success-color:', theme_css)
        self.assertIn('--warning-color:', theme_css)
        self.assertIn('--error-color:', theme_css)
        self.assertIn('--info-color:', theme_css)
        
        # Check opacity variants are generated
        self.assertIn('--primary-color-25:', theme_css)
        self.assertIn('--primary-color-50:', theme_css)
        self.assertIn('--primary-color-75:', theme_css)
    
    def test_custom_theme_colors_in_css(self):
        """Test that custom theme colors are reflected in generated CSS."""
        from django_spellbook.theme import generate_theme_css
        
        # Configure custom theme
        theme_config = {
            'colors': {
                'primary': '#FF0000',
                'secondary': '#00FF00',
            }
        }
        
        # Get the generated CSS
        theme_css = generate_theme_css(theme_config)
        
        # Check custom colors are in CSS
        self.assertIn('--primary-color: #FF0000;', theme_css)
        self.assertIn('--secondary-color: #00FF00;', theme_css)
        
        # Check opacity variants for custom colors
        self.assertIn('--primary-color-25: color-mix(in srgb, #FF0000 25%, transparent);', theme_css)
        self.assertIn('--primary-color-50: color-mix(in srgb, #FF0000 50%, transparent);', theme_css)
        self.assertIn('--primary-color-75: color-mix(in srgb, #FF0000 75%, transparent);', theme_css)


class TestThemePresetIntegration(TestCase):
    """Test theme preset integration with template tags."""
    
    def test_all_preset_themes_generate_valid_css(self):
        """Test that all preset themes generate valid CSS."""
        from django_spellbook.theme import THEMES, generate_theme_css
        
        for theme_name, theme_config in THEMES.items():
            with self.subTest(theme=theme_name):
                # Generate CSS for this theme
                theme_css = generate_theme_css(theme_config)
                
                # Basic validation
                self.assertIn(':root {', theme_css)
                self.assertIn('--primary-color:', theme_css)
                
                # Check that color values are present (not empty)
                lines = theme_css.split('\n')
                for line in lines:
                    if '--primary-color:' in line and ';' in line:
                        # Extract the value between : and ;
                        value = line.split(':')[1].split(';')[0].strip()
                        self.assertTrue(
                            value and value != 'transparent',
                            f"Theme {theme_name} has invalid primary color"
                        )
                        break
    
    def test_theme_css_includes_all_semantic_colors(self):
        """Test that generated CSS includes all semantic color categories."""
        from django_spellbook.templatetags.spellbook_tags import spellbook_styles
        
        context = spellbook_styles()
        theme_css = context['theme_css']
        
        # All semantic colors should be defined
        semantic_colors = [
            'primary', 'secondary', 'accent', 'neutral',
            'success', 'warning', 'error', 'info'
        ]
        
        for color_name in semantic_colors:
            with self.subTest(color=color_name):
                # Check base color
                self.assertIn(f'--{color_name}-color:', theme_css)
                # Check opacity variants
                self.assertIn(f'--{color_name}-color-25:', theme_css)
                self.assertIn(f'--{color_name}-color-50:', theme_css)
                self.assertIn(f'--{color_name}-color-75:', theme_css)
    
    def test_template_rendering_with_theme_styles(self):
        """Test that templates can use theme styles correctly."""
        # Create a test template that uses spellbook_styles
        template_string = """
        {% load spellbook_tags %}
        {% spellbook_styles %}
        <div class="sb-bg-primary sb-text-white">Test</div>
        """
        
        template = Template(template_string)
        rendered = template.render(Context())
        
        # Check that styles are included
        self.assertIn('django_spellbook/css_modules/utilities/colors.css', rendered)
        self.assertIn(':root {', rendered)
        self.assertIn('--primary-color:', rendered)
        
        # Check that the div with utility classes is present
        self.assertIn('class="sb-bg-primary sb-text-white"', rendered)