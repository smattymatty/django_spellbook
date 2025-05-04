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
from django_spellbook.markdown.extensions.custom_tag_parser import (
    NestedTagError
)

import logging


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
        
    def test_id_shortcut_with_explicit_id(self):
        """Test ID shortcut syntax"""
        text = '{% div id="myid" %}content{% enddiv %}'
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
            '<div class="outer"><span class="inner"><p>nested content</p></span></div>', html)

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
        
    #@unittest.expectedFailure
    def test_django_block_with_markdown(self):
        """Test Django block tags with markdown content"""
        text = '''{% if condition %} Yoo {% endif %}
**bold** and _italic_ssor)
Test nested custom elements
# Heading
{% div .content %}
**Bold text**
{% static "style.css" %}

{% span %}nested{% endspan %}
{% enddiv %}'''
        html = self.md.convert(text)
        self.assertIn("<django-tag>{% if condition %}</django-tag>", html)
        self.assertIn('<h1>Heading</h1>', html)
        self.assertIn('<div class="content">', html)
        self.assertIn('<strong>Bold text</strong>', html)
        self.assertIn('{% static "style.css" %}', html)
        self.assertIn('<django-tag>{% static "style.css" %}</django-tag></p>\n<span>', html)

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
        self.assertIn('<p>content</p>', html)
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
        text = '''{% div %}content{% enddiv %}'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('content', html)
        self.assertNotIn('{% enddiv %}', html)

    def test_clean_end_tags_removal_with_many_tags(self):
        """Test complete removal of end tags from content"""
        text = '''{% div %}content{% enddiv %}
{% span %}more content{% endspan %}'''
        html = self.md.convert(text)
        self.assertIn('<div>', html)
        self.assertIn('content', html)
        self.assertIn('<span>', html)
        self.assertIn('more content', html)
        self.assertNotIn('{% endspan %}', html)
        self.assertNotIn('{% enddiv %}', html)
    
    def test_clean_end_tags_removal_with_unexpected_end(self):
        """Test complete removal of end tags from content"""
        text = '''{% div %}
            content
            {% endspan %}
            more content
            {% enddiv %}'''
        with self.assertRaises(NestedTagError) as cm:
            self.md.convert(text)
            self.assertIn('Found end tag', str(cm.exception))

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

class TestDjangoLikeTagProcessorCoverage(TestCase):
    """
    Tests specifically targeting block handling and edge cases for coverage
    in DjangoLikeTagProcessor.
    """
    def setUp(self):
        # Create a fresh markdown instance for each test
        self.md = markdown.Markdown(extensions=[DjangoLikeTagExtension()])

    def test_custom_tag_spanning_multiple_blocks(self):
            """
            Covers _process_nested_content block iteration:
            - `if remaining_blocks:`
            - `current_content = remaining_blocks.pop(0)`
            - newline insertion between blocks
            - finding end tag in a later block (`elif end_match:`)
            """
            # REMOVE indentation from content lines
            text = '''{% section .hero %}
Content Block 1.

Content Block 2.
{% endsection %}
After Section.'''
            html = self.md.convert(text)

            # Check structure
            self.assertIn('<section class="hero">', html)
            self.assertIn('</section>', html)
            # This assertion should now pass
            self.assertIn('<p>After Section.</p>', html)

            # Check content preservation and structure across blocks
            self.assertIn('<p>Content Block 1.\n', html) # TODO: look into whether or not this is correct
            self.assertIn('Content Block 2.</p>', html) # Do We want a newline, or to wrap it in a <p>?

            # Ensure content before/after the tag is correct
            self.assertTrue(html.strip().startswith('<section class="hero">'))
            # This assertion should also pass now
            self.assertTrue(html.strip().endswith('<p>After Section.</p>'))

            # Ensure end tag is removed
            self.assertNotIn('{% endsection %}', html)

    def test_trailing_content_within_block_handled(self):
        """
        Covers _process_nested_content else path for no more tags:
        - `content_after_last_tag = current_content[...]`
        - `collected_content_parts.append(content_after_last_tag)`
        Also tests finding start tag (`elif start_match:`)
        """
        text = '''{% div %}Start of block. {% span %}Nested{% endspan %} End of block content.{% enddiv %}'''
        html = self.md.convert(text)

        self.assertIn('<div>', html)
        # Check that content both before and after the nested tag is captured
        # Markdown might wrap these in separate <p> or process inline
        self.assertIn('Start of block.', html)
        self.assertIn('<span><p>Nested</p></span>', html)
        self.assertIn('End of block content.', html)
        self.assertIn('</div>', html)

        # Ensure tags are removed from final output text
        self.assertNotIn('{% span %}', html)
        self.assertNotIn('{% endspan %}', html)
        self.assertNotIn('{% enddiv %}', html)

    def test_django_tag_with_trailing_content_in_same_block(self):
        """
        Covers _handle_django_block_tag:
        - `if after_content:`
        - `blocks.insert(0, after_content)`
        """
        text = '''Before. {% if condition %}Inside if.{% endif %} After if in same block.'''
        html = self.md.convert(text)

        # Check preservation of Django tags
        self.assertIn('<django-tag>{% if condition %}</django-tag>', html)
        self.assertIn('<django-tag>{% endif %}</django-tag>', html)

        # Check content placement
        self.assertIn('<p>Before. </p>', html) # Markdown wraps blocks
        self.assertIn('<p>Inside if.</p>', html)
        self.assertIn('<p>After if in same block.</p>', html)

        # Verify order if possible (might be tricky with <p> tags)
        # A rough check:
        if_tag_index = html.find('<django-tag>{% if condition %}</django-tag>')
        inside_if_index = html.find('<p>Inside if.</p>')
        endif_tag_index = html.find('<django-tag>{% endif %}</django-tag>')
        after_if_index = html.find('<p>After if in same block.</p>')

        self.assertTrue(0 < if_tag_index < inside_if_index < endif_tag_index < after_if_index)

    # Inside TestDjangoLikeTagProcessorCoverage class...

    def test_start_tag_at_block_end(self):
        """
        Covers _process_nested_content `elif start_match:` specifically.
        A block ends immediately after a start tag is opened.
        """
        # Note: The blank line creates the block boundary after {% span %}
        text = '''{% div %}
Block 1 content. {% span %}

Block 2 span content. {% endspan %} Block 2 div content.
{% enddiv %}'''
        html = self.md.convert(text)

        # Check structure and content
        self.assertIn('<div>', html)
        self.assertIn('<p>Block 1 content. </p>', html) # Content before span
        self.assertIn('<span>', html)
        self.assertIn('<p>Block 2 span content.</p>', html) # Span content from next block
        self.assertIn('</span>', html)
        self.assertIn('<p>Block 2 div content.</p>', html) # Div content after span in 2nd block
        self.assertIn('</div>', html)

        # Check tag removal
        self.assertNotIn('{% span %}', html)
        self.assertNotIn('{% endspan %}', html)
        self.assertNotIn('{% enddiv %}', html)
        # Check ordering (approximate)
        self.assertTrue(html.find('<p>Block 1 content.</p>') < html.find('<span>'))
        self.assertTrue(html.find('</span>') < html.find('<p>Block 2 div content.</p>'))


    def test_end_tag_at_block_start(self):
        """
        Covers _process_nested_content `elif end_match:` specifically.
        A block starts immediately with the required end tag.
        """
        # Note: Blank line creates block boundary before {% enddiv %}
        text = '''{% div %}
Content in block 1.

{% enddiv %}
Content after block.''' # {% enddiv %} starts the second block
        html = self.md.convert(text)

        # Check structure and content
        self.assertIn('<div>', html)
        self.assertIn('<p>Content in block 1.</p>', html)
        self.assertIn('</div>', html)
        self.assertIn('<p>Content after block.</p>', html)

        # Check tag removal
        self.assertNotIn('{% enddiv %}', html)
        # Check ordering (approximate)
        self.assertTrue(html.find('</div>') < html.find('<p>Content after block.</p>'))
        
    # Add this test method to your TestDjangoLikeTagProcessorCoverage class

    def test_elif_end_match_after_nested_tag(self):
        """
        Covers _process_nested_content `elif end_match:` specifically.
        Ensures this path is taken when searching for an outer tag's end
        after a nested block has been processed and closed.
        """
        text = '''{% outer %}
Content A
{% inner %}Inner Content{% endinner %}
Content B
{% endouter %}'''
        # Ensure no indentation issues affect parsing this time
        html = self.md.convert(text)

        # Basic structure checks
        self.assertIn('<outer>', html)
        self.assertIn('</outer>', html)
        self.assertIn('<inner>', html)
        self.assertIn('</inner>', html)

        # Content checks (Markdown adds <p> tags)
        # Depending on how parseBlocks handles the recursive call and content splitting,
        # 'Content A' and 'Content B' might end up in the same <p> tag or separate ones
        # before/after the inner element. Let's check for presence.
        self.assertIn('Content A', html)
        self.assertIn('<p>Inner Content</p>', html) # Inner content usually gets its own <p>
        self.assertIn('Content B', html)

        # Ensure correct nesting in output (simple check)
        outer_start = html.find('<outer>')
        inner_start = html.find('<inner>')
        inner_end = html.find('</inner>')
        outer_end = html.find('</outer>')
        # Check that inner is fully contained within outer
        self.assertTrue(0 <= outer_start < inner_start < inner_end < outer_end,
                        "HTML nesting order is incorrect.")

        # Ensure processor tags are removed from the final HTML
        self.assertNotIn('{% inner %}', html)
        self.assertNotIn('{% endinner %}', html)
        self.assertNotIn('{% endouter %}', html)