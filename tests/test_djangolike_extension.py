import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree
import markdown
from django.test import TestCase
from django_spellbook.markdown.extensions.django_like import (
    DjangoLikeTagProcessor,
    DjangoLikeTagExtension,
    makeExtension
)


class TestDjangoLikeTagProcessor(TestCase):
    def setUp(self):
        self.md = markdown.Markdown(extensions=[DjangoLikeTagExtension()])
        self.processor = DjangoLikeTagProcessor(self.md.parser)

    def test_custom_element_basic(self):
        """Test basic custom element processing"""
        text = '{% div class="test" %}content{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn('<div class="test">\n<p>content</p>\n</div>', html)

    def test_custom_element_with_markdown(self):
        """Test custom element with markdown content"""
        text = '{% div %}**bold** _italic_{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn(
            '<div>\n<p><strong>bold</strong> <em>italic</em></p>\n</div>', html)

    def test_class_shortcut(self):
        """Test class shortcut syntax"""
        text = '{% div .class1 .class2 %}content{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn(
            '<div class="class1 class2">\n<p>content</p>\n</div>', html)

    def test_id_shortcut(self):
        """Test ID shortcut syntax"""
        text = '{% div #myid %}content{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn('<div id="myid">\n<p>content</p>\n</div>', html)

    def test_mixed_attributes(self):
        """Test mixed attribute syntaxes"""
        text = '{% div .class1 #myid data-test="value" %}content{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn('class="class1"', html)
        self.assertIn('id="myid"', html)
        self.assertIn('data-test="value"', html)

    def test_nested_elements(self):
        """Test nested custom elements"""
        text = '''{% div .outer %}
            {% span .inner %}nested content{% endspan %}
        {% enddiv %}'''
        html = self.md.convert(text)
        self.assertIn('<div class="outer">', html)
        self.assertIn(
            '<div class="outer"><span class="inner"><p>nested content\n        </p></span></div', html)

    def test_django_static_tag(self):
        """Test preservation of Django static tag"""
        text = '{% static "path/to/file.css" %}'
        html = self.md.convert(text)
        self.assertIn('{% static "path/to/file.css" %}', html)

    def test_django_url_tag(self):
        """Test preservation of Django URL tag"""
        text = '{% url "view-name" arg1 arg2 %}'
        html = self.md.convert(text)
        self.assertIn('{% url "view-name" arg1 arg2 %}', html)

    def test_django_include_tag(self):
        """Test preservation of Django include tag"""
        text = '{% include "template_name.html" %}'
        html = self.md.convert(text)
        self.assertIn('{% include "template_name.html" %}', html)

    def test_django_if_tag(self):
        """Test preservation of Django if tag block"""
        text = '''{% if condition %}
            content
        {% endif %}'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('<django-tag>{% endif %}</django-tag>', html)

    def test_django_for_tag(self):
        """Test preservation of Django for tag block"""
        text = '''{% for item in items %}
            {{ item }}
        {% endfor %}'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% for item in items %}</django-tag>', html)
        self.assertIn('<django-tag>{% endfor %}</django-tag>', html)

    def test_nested_django_tags(self):
        """Test nested Django template tags"""
        text = '''{% if outer %}
            {% for item in items %}
                {{ item }}
            {% endfor %}
        {% endif %}'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if outer %}</django-tag>', html)
        self.assertIn('<django-tag>{% for item in items %}</django-tag>', html)
        self.assertIn('<django-tag>{% endfor %}</django-tag>', html)
        self.assertIn('<django-tag>{% endif %}</django-tag>', html)

    def test_django_block_with_markdown(self):
        """Test Django block tags with markdown content"""
        text = '''{% if condition %}
**bold** and _italic_
{% endif %}'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('<strong>bold</strong>', html)
        self.assertIn('<em>italic</em>', html)
        self.assertIn('<django-tag>{% endif %}</django-tag>', html)

    def test_mixed_content(self):
        """Test mixing markdown, custom elements, and Django tags"""
        text = '''# Heading
{% div .content %}
**Bold text**
{% static "style.css" %}
{% span %}nested{% endspan %}
{% enddiv %}'''
        html = self.md.convert(text)
        self.assertIn('<h1>Heading</h1>', html)
        self.assertIn('<div class="content">', html)
        self.assertIn('<strong>Bold text</strong>', html)
        self.assertIn('{% static "style.css" %}', html)
        self.assertIn('<span><p>nested\n</p></span>', html)

    def test_error_handling(self):
        """Test error handling in attribute parsing"""
        text = '{% div invalid"attribute %}content{% enddiv %}'
        html = self.md.convert(text)
        self.assertIn('<div>\n<p>content</p>\n</div>', html)

    def test_remaining_content_after_end_tag(self):
        """Test handling of remaining content after end tag"""
        text = '''{% div %}
content
{% enddiv %}
remaining content'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('<p>content\n</p>', html)
        self.assertIn('<p>remaining content</p>', html)

    def test_missing_end_tag_content_preservation(self):
        """Test content preservation when end tag is missing"""
        text = '''{% if condition %}
            content without end tag'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('content without end tag', html)

    def test_block_tag_across_multiple_blocks(self):
        """Test handling of block tags spanning multiple blocks"""
        text = '''{% if condition %}
            first block

            second block

            third block
            {% endif %}'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('first block', html)
        self.assertIn('second block', html)
        self.assertIn('third block', html)
        self.assertIn('<django-tag>{% endif %}</django-tag>', html)

    def test_clean_end_tags_removal(self):
        """Test complete removal of end tags from content"""
        text = '''{% div %}
            content
            {% endspan %}
            more content
            {% enddiv %}'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('content', html)
        self.assertIn('more content', html)
        self.assertNotIn('{% endspan %}', html)
        self.assertNotIn('{% enddiv %}', html)

    def test_remaining_blocks_with_content(self):
        """Test handling of remaining blocks with content after tag processing"""
        text = '''{% div %}
            first content
            {% enddiv %}
            second content
            
            third content'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('first content', html)
        self.assertIn('second content', html)
        self.assertIn('third content', html)

    def test_nested_tags_with_remaining_content(self):
        """Test handling of nested tags with remaining content"""
        text = '''{% div %}
            {% span %}inner content{% endspan %}
            remaining div content
            {% enddiv %}
            after div content'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('<span>', html)
        self.assertIn('inner content', html)
        self.assertIn('remaining div content', html)
        self.assertIn('after div content', html)
        self.assertNotIn('{% endspan %}', html)
        self.assertNotIn('{% enddiv %}', html)

    def test_block_tag_without_end_tag(self):
        """Test handling of block tags without corresponding end tags"""
        text = '''{% if condition %}
            content in if block
            {% for item in items %}
            loop content'''
        html = self.md.convert(text)
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('content in if block', html)
        self.assertIn('<django-tag>{% for item in items %}</django-tag>', html)
        self.assertIn('loop content', html)

    def test_end_tag_replacement(self):
        """Test the end tag replacement function"""
        processor = DjangoLikeTagProcessor(self.md.parser)
        content = '''content
        {% endtag %}
        more content
        {% endanother %}'''
        cleaned = processor._clean_end_tags(content)
        self.assertEqual(cleaned, '''content
        
        more content
        ''')

    def test_run_with_no_match(self):
        """Test run method when there's no match for Django-like tags"""
        processor = DjangoLikeTagProcessor(self.md.parser)
        parent = ElementTree.Element('div')
        blocks = ['Regular text without any tags']
        result = processor.run(parent, blocks)
        self.assertFalse(result)

    def test_make_extension_basic(self):
        """Test makeExtension function with no arguments"""
        ext = makeExtension()
        self.assertIsInstance(ext, DjangoLikeTagExtension)
