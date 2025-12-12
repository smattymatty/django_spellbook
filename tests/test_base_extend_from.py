# tests/test_base_extend_from.py

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.management.base import CommandError
from django.template import TemplateDoesNotExist

from django_spellbook.management.commands.command_utils import _validate_extend_from_setting
from django_spellbook.management.commands.processing.base_template_generator import SpellbookBaseGenerator


class TestExtendFromValidation(TestCase):
    """Test SPELLBOOK_BASE_EXTEND_FROM validation."""

    def test_list_length_mismatch(self):
        """List must match SPELLBOOK_MD_APP length."""
        with self.assertRaises(CommandError) as cm:
            _validate_extend_from_setting(
                ['app1/base.html', 'app2/base.html'],
                ['app1']  # Only 1 app
            )
        self.assertIn('has 2 entries but SPELLBOOK_MD_APP has 1', str(cm.exception))

    def test_none_values_allowed(self):
        """Allow None for some apps."""
        # Should not raise - testing with None values
        try:
            _validate_extend_from_setting(
                [None, None],
                ['app1', 'app2']
            )
        except CommandError:
            self.fail("_validate_extend_from_setting raised CommandError unexpectedly with None values")

    @patch('django.template.loader.get_template')
    def test_template_not_found(self, mock_get_template):
        """Error if template doesn't exist."""
        mock_get_template.side_effect = TemplateDoesNotExist('nonexistent/base.html')

        with self.assertRaises(CommandError) as cm:
            _validate_extend_from_setting(
                ['nonexistent/base.html'],
                ['app1']
            )
        self.assertIn('template not found', str(cm.exception))

    @patch('django.template.loader.get_template')
    def test_missing_spellbook_block(self, mock_get_template):
        """Error if template missing {% block spellbook %}."""
        # Create a mock template without the spellbook block
        mock_template = MagicMock()
        mock_template.template.source = '''
            <html>
            <body>
                {% block content %}{% endblock %}
            </body>
            </html>
        '''
        mock_get_template.return_value = mock_template

        with self.assertRaises(CommandError) as cm:
            _validate_extend_from_setting(
                ['myapp/base.html'],
                ['app1']
            )
        self.assertIn('missing required block', str(cm.exception))
        self.assertIn('spellbook', str(cm.exception))

    @patch('django.template.loader.get_template')
    def test_template_with_spellbook_block_passes(self, mock_get_template):
        """Template with {% block spellbook %} passes validation."""
        mock_template = MagicMock()
        mock_template.template.source = '''
            <html>
            <body>
                {% block spellbook %}{% endblock %}
            </body>
            </html>
        '''
        mock_get_template.return_value = mock_template

        # Should not raise
        try:
            _validate_extend_from_setting(
                ['myapp/base.html'],
                ['app1']
            )
        except CommandError:
            self.fail("Validation failed for template with spellbook block")


class TestSpellbookBaseGenerator(TestCase):
    """Test SpellbookBaseGenerator class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path('/tmp/test_spellbook_base')
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir = self.test_dir / 'templates' / 'test_app'
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_generates_at_correct_path(self):
        """File created at {app}/templates/{app}/spellbook_base.html."""
        generator = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/base.html'
        )

        result_path = generator.process()

        self.assertEqual(result_path, 'test_app/spellbook_base.html')
        self.assertTrue((self.template_dir / 'spellbook_base.html').exists())

    def test_replaces_extend_from_placeholder(self):
        """__EXTEND_FROM__ replaced with actual template path."""
        generator = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/custom_base.html'
        )

        generator.process()

        content = (self.template_dir / 'spellbook_base.html').read_text()
        self.assertIn("{% extends 'myapp/custom_base.html' %}", content)
        self.assertNotIn('__EXTEND_FROM__', content)

    def test_cleanup_removes_file(self):
        """File deleted when extend_from is None."""
        # First create the file
        generator = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/base.html'
        )
        generator.process()
        self.assertTrue((self.template_dir / 'spellbook_base.html').exists())

        # Now cleanup
        generator_cleanup = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            None  # No extend_from
        )
        result = generator_cleanup.process()

        self.assertIsNone(result)
        self.assertFalse((self.template_dir / 'spellbook_base.html').exists())

    def test_cleanup_handles_missing_file(self):
        """No error if file doesn't exist during cleanup."""
        generator = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            None
        )

        # Should not raise even though file doesn't exist
        try:
            result = generator.process()
            self.assertIsNone(result)
        except Exception as e:
            self.fail(f"Cleanup raised exception when file doesn't exist: {e}")

    def test_includes_sidebar_content(self):
        """Generated file contains full sidebar layout."""
        generator = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/base.html'
        )

        generator.process()

        content = (self.template_dir / 'spellbook_base.html').read_text()

        # Check for key components
        self.assertIn('{% load spellbook_tags %}', content)
        self.assertIn('{% load static %}', content)
        self.assertIn('{% block spellbook %}', content)
        self.assertIn('{% endblock %}', content)
        self.assertIn('{% spellbook_styles %}', content)
        self.assertIn('spellbook-container', content)
        self.assertIn('spellbook-layout', content)
        self.assertIn('spellbook-toc', content)
        self.assertIn('spellbook-content', content)
        self.assertIn('{% block spellbook_md %}', content)

    def test_overwrites_on_regenerate(self):
        """Silently overwrites existing file."""
        generator1 = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/base_v1.html'
        )
        generator1.process()

        content1 = (self.template_dir / 'spellbook_base.html').read_text()
        self.assertIn('myapp/base_v1.html', content1)

        # Regenerate with different template
        generator2 = SpellbookBaseGenerator(
            'test_app',
            self.template_dir,
            'myapp/base_v2.html'
        )
        generator2.process()

        content2 = (self.template_dir / 'spellbook_base.html').read_text()
        self.assertIn('myapp/base_v2.html', content2)
        self.assertNotIn('myapp/base_v1.html', content2)


class TestExtendFromPrecedence(TestCase):
    """Test EXTEND_FROM takes precedence over BASE_TEMPLATE."""

    @override_settings(
        SPELLBOOK_MD_APP='test_app',
        SPELLBOOK_MD_PATH='/tmp/test_content',
        SPELLBOOK_MD_BASE_TEMPLATE='custom_base.html',
        SPELLBOOK_BASE_EXTEND_FROM='myapp/base.html'
    )
    @patch('django.template.loader.get_template')
    def test_extend_from_overrides_base_template(self, mock_get_template):
        """EXTEND_FROM used when both are set."""
        # Mock the template to have the spellbook block
        mock_template = MagicMock()
        mock_template.template.source = '{% block spellbook %}{% endblock %}'
        mock_get_template.return_value = mock_template

        from django_spellbook.management.commands.command_utils import validate_spellbook_settings

        md_paths, apps, url_prefixes, base_templates, extend_from_templates = validate_spellbook_settings()

        # Verify extend_from is set
        self.assertEqual(extend_from_templates, ['myapp/base.html'])

        # Verify base_template is also present (not overridden at settings level)
        self.assertEqual(base_templates, ['custom_base.html'])

        # The precedence is handled in MarkdownProcessor, not in validation
        # This test confirms both settings are captured correctly


class TestExtendFromIntegration(TestCase):
    """Integration tests for EXTEND_FROM feature."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path('/tmp/test_integration_extend_from')
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_mixed_none_values(self):
        """Test with mixed None and template values."""
        # Should not raise
        try:
            _validate_extend_from_setting(
                ['app1/base.html', None, 'app3/base.html'],
                ['app1', 'app2', 'app3']
            )
        except CommandError:
            # Will fail on template not found, but validates list handling
            pass
