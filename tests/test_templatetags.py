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
        """Test that spellbook_styles tag returns context with theme_css"""
        result = spellbook_styles()
        # Should return a dictionary with theme_css key
        self.assertIsInstance(result, dict)
        self.assertIn('theme_css', result)
        # Theme CSS should be a string containing CSS variables
        self.assertIsInstance(result['theme_css'], str)
        self.assertIn(':root {', result['theme_css'])
        self.assertIn('--primary-color:', result['theme_css'])


class TestDashStrip(TestCase):
    def test_dash_strip(self):
        """Test that dash_strip removes the initial dashes from a string"""
        result = dash_strip('--test-string')
        self.assertEqual(result, 'test-string')


@override_settings(TEMPLATES=settings.TEMPLATES)
class TestPageHeader(TestCase):
    @patch('django_spellbook.templatetags.spellbook_tags.reverse')
    def test_page_header_with_full_context(self, mock_reverse):
        """Test page_header with complete context including all fields"""
        # Mock reverse to return test URLs
        mock_reverse.side_effect = lambda x: f'/{x}/'

        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'metadata': {
                'title': 'Test Page',
                'author': 'Test Author',
                'prev_page': 'test:prev',
                'next_page': 'test:next',
            },
            'parent_directory_url': 'parent/',
            'parent_directory_name': 'Parent Directory',
        })

        result = template.render(context)

        # Check that key elements are present
        self.assertIn('Test Page', result)
        self.assertIn('Test Author', result)
        # Note: "Back to" link is now in base template, not page_header
        self.assertIn('Previous', result)
        self.assertIn('Next', result)

    @patch('django_spellbook.templatetags.spellbook_tags.reverse')
    def test_page_header_at_content_root(self, mock_reverse):
        """Test page_header at content root (links back to directory index)"""
        # Mock reverse to return test URLs
        mock_reverse.side_effect = lambda x: f'/{x}/'

        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'metadata': {
                'title': 'Root Page',
                'author': None,
                'prev_page': None,
                'next_page': None,
            },
            'parent_directory_url': 'content:content_directory_index_directory_index_root_content',
            'parent_directory_name': 'Content',
        })

        result = template.render(context)

        # Should have title (back button is now in base template, not page_header)
        self.assertIn('Root Page', result)
        # Note: "Back to" link is now in base template, not page_header
        # Check that nav button text is not present (not just in HTML comments)
        self.assertNotIn('<span class="sb-text-sm">Previous</span>', result)
        self.assertNotIn('<span class="sb-text-sm">Next</span>', result)

    def test_page_header_without_author(self):
        """Test page_header with no author"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'metadata': {
                'title': 'No Author Page',
                'author': None,
            },
        })

        result = template.render(context)

        self.assertIn('No Author Page', result)
        self.assertNotIn('by ', result)

    @patch('django_spellbook.templatetags.spellbook_tags.reverse')
    def test_page_header_with_only_prev(self, mock_reverse):
        """Test page_header with only previous page"""
        # Mock reverse to return test URLs
        mock_reverse.side_effect = lambda x: f'/{x}/'

        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'metadata': {
                'title': 'Middle Page',
                'prev_page': 'test:prev',
                'next_page': None,
            },
        })

        result = template.render(context)

        self.assertIn('Previous', result)
        # Check that "Next" button text is not present (not just in HTML comments)
        self.assertNotIn('<span class="sb-text-sm">Next</span>', result)

    @patch('django_spellbook.templatetags.spellbook_tags.reverse')
    def test_page_header_with_only_next(self, mock_reverse):
        """Test page_header with only next page"""
        # Mock reverse to return test URLs
        mock_reverse.side_effect = lambda x: f'/{x}/'

        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'metadata': {
                'title': 'First Page',
                'prev_page': None,
                'next_page': 'test:next',
            },
        })

        result = template.render(context)

        # Check that "Previous" button text is not present (not just in HTML comments)
        self.assertNotIn('<span class="sb-text-sm">Previous</span>', result)
        self.assertIn('<span class="sb-text-sm">Next</span>', result)

    def test_page_header_with_empty_context(self):
        """Test page_header with empty context"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({})

        result = template.render(context)

        # Should return empty string or minimal output
        self.assertIsInstance(result, str)

    def test_page_header_for_directory_with_name(self):
        """Test page_header for directory index with directory_name set"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'is_directory_index': True,
            'directory_name': 'My Folder',
            'directory_path': 'my_folder/',
        })

        result = template.render(context)

        self.assertIn('My Folder', result)
        self.assertNotIn('None', result)

    def test_page_header_for_directory_without_name(self):
        """Test page_header for directory index without directory_name (fallback to directory_path)"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'is_directory_index': True,
            'directory_name': None,  # Missing or None
            'directory_path': 'api_docs/',
        })

        result = template.render(context)

        # Should extract from directory_path and humanize it
        self.assertIn('Api Docs', result)
        self.assertNotIn('None', result)

    def test_page_header_for_directory_no_name_no_path(self):
        """Test page_header for directory index without directory_name or directory_path (fallback to 'Content')"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_header %}"
        )
        context = Context({
            'is_directory_index': True,
            'directory_name': None,
            'directory_path': '',
        })

        result = template.render(context)

        # Should use 'Content' as fallback
        self.assertIn('Content', result)
        self.assertNotIn('None', result)


@override_settings(TEMPLATES=settings.TEMPLATES)
class TestPageMetadata(TestCase):
    def test_page_metadata_alias(self):
        """Test that page_metadata is an alias for show_metadata"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_metadata %}"
        )
        context = Context({
            'metadata': {
                'published': None,
                'modified': None,
                'tags': [],
            },
        })

        # Should render without errors
        result = template.render(context)
        self.assertIsInstance(result, str)

    def test_page_metadata_for_dev(self):
        """Test page_metadata with for_dev parameter"""
        template = Template(
            "{% load spellbook_tags %}"
            "{% page_metadata 'for_dev' %}"
        )
        context = Context({
            'metadata': {
                'published': None,
                'modified': None,
                'tags': [],
            },
        })

        # Should render without errors
        result = template.render(context)
        self.assertIsInstance(result, str)
