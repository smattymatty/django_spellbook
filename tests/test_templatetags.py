import unittest
from unittest.mock import patch, Mock

from django.template import Template, Context
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from django_spellbook.templatetags.spellbook_tags import sidebar_toc, TOC
from django.urls import reverse, NoReverseMatch
from django_spellbook.templatetags.spellbook_tags import spellbook_url, spellbook_styles, dash_strip

from . import settings


@override_settings(TEMPLATES=settings.TEMPLATES)
class TestSpellbookTags(TestCase):
    def setUp(self):
        """Set up the test environment before each test"""
        self.template = Template(
            "{% load spellbook_tags %}"
            "{% sidebar_toc %}"
        )
        self.metadata_template = Template(
            "{% load spellbook_tags %}"
            "{% show_metadata %}"
        )

    def test_returns_toc(self):
        """Test that sidebar_toc returns an empty dictionary"""
        result = sidebar_toc(Context({'toc': TOC}))
        self.assertEqual(result['toc'], TOC)

    def test_empty_sidebar_toc_tag(self):
        """Test that sidebar_toc raises ImproperlyConfigured when TOC is missing"""
        context = Context({})
        with self.assertRaises(ImproperlyConfigured) as cm:
            self.template.render(context)
        self.assertIn("is required", str(cm.exception))

    def test_sidebar_toc_tag_with_none_toc(self):
        """Test that sidebar_toc handles None TOC appropriately"""
        context = Context({'toc': None})
        with self.assertRaises(ImproperlyConfigured) as cm:
            self.template.render(context)
        self.assertIn("is required", str(cm.exception))


class TestSpellbookUrl(TestCase):
    def test_valid_url_path(self):
        """Test spellbook_url with a valid URL path that can be reversed"""
        with patch('django_spellbook.templatetags.spellbook_tags.reverse') as mock_reverse:
            # Setup mock to return a known URL
            mock_reverse.return_value = '/test/url/'

            # Test with a simple path
            result = spellbook_url('test_page')

            # Verify the result
            self.assertEqual(result, '/test/url/')
            mock_reverse.assert_called_once_with('test_page')

    def test_invalid_url_path(self):
        """Test spellbook_url with an invalid URL path that cannot be reversed"""
        with patch('django_spellbook.templatetags.spellbook_tags.reverse') as mock_reverse:
            # Setup mock to raise NoReverseMatch
            mock_reverse.side_effect = NoReverseMatch()

            # Test with an invalid path
            result = spellbook_url('docs:__getitem__')

            # Verify fallback behavior
            self.assertEqual(result, 'docs:__getitem__ xx Not Found')

    def test_empty_url_path(self):
        """Test spellbook_url with an empty URL path"""
        result = spellbook_url('')
        self.assertEqual(result, '#')

    def test_special_characters_url_path(self):
        """Test spellbook_url with special characters in the URL path"""
        with patch('django_spellbook.templatetags.spellbook_tags.reverse') as mock_reverse:
            # Setup mock to return a known URL
            mock_reverse.return_value = '/special/url/'

            # Test with a path containing special characters
            result = spellbook_url('special_page@#$')

            # Verify the result
            self.assertEqual(result, '/special/url/')
            mock_reverse.assert_called_once_with('special_page@#$')


class TestSpellbookStyles(TestCase):
    def test_spellbook_styles_tag(self):
        """Test that spellbook_styles tag returns an empty dictionary"""
        result = spellbook_styles()
        self.assertEqual(result, {})


class TestDashStrip(TestCase):
    def test_dash_strip(self):
        """Test that dash_strip removes the initial dashes from a string"""
        result = dash_strip('--test-string')
        self.assertEqual(result, 'test-string')
