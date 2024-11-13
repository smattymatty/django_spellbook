# tests/test_markdown.py
from django.test import TestCase
from django_spellbook.markdown.parser import MarkdownParser


class BasicMarkdownTest(TestCase):
    """Test basic markdown parsing capabilities"""

    def test_basic_text(self):
        """Test basic text parsing"""
        md = "This is a test"
        parser = MarkdownParser(md)
        self.assertEqual(parser.get_html(), "<p>This is a test</p>")

    def test_headers(self):
        """Test header parsing"""
        md = "# H1\n## H2\n### H3"
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn("<h1>H1</h1>", html)
        self.assertIn("<h2>H2</h2>", html)
        self.assertIn("<h3>H3</h3>", html)

    def test_emphasis(self):
        """Test emphasis parsing"""
        md = "*italic* **bold** ***both***"
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn("<em>italic</em>", html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<strong><em>both</em></strong>", html)

    def test_lists(self):
        """Test list parsing"""
        md = """- Item 1
- Item 2

1. First
2. Second"""  # Added blank line between lists
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn("<ul>", html)
        self.assertIn("<ol>", html)
        self.assertIn("<li>Item 1</li>", html)
        self.assertIn("<li>First</li>", html)

    def test_code_blocks(self):
        """Test code block parsing"""
        md = "```python\ndef test():\n    pass\n```"
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('<pre><code class="language-python">', html)
        self.assertIn("def test():", html)


class DjangoLikeTest(TestCase):
    """Test Django-like tag parsing and attribute handling"""

    def test_basic_div(self):
        """Test basic div with class and id"""
        md = """{% div .my-class #my-id %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('<div class="my-class" id="my-id">', html)
        self.assertIn('Content', html)

    def test_multiple_classes(self):
        """Test multiple classes"""
        md = """{% div .class1 .class2 .class3 %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('<div class="class1 class2 class3">', html)

    def test_htmx_attributes(self):
        """Test HTMX attributes"""
        md = """{% div hx-get="/api/data" hx-swap="outerHTML" hx-trigger="click" %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('hx-get="/api/data"', html)
        self.assertIn('hx-swap="outerHTML"', html)
        self.assertIn('hx-trigger="click"', html)

    def test_alpine_attributes(self):
        """Test Alpine.js attributes"""
        md = """{% div x-data="{open: false}" x-show="open" @click="open = !open" %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('x-data="{open: false}"', html)
        self.assertIn('x-show="open"', html)
        self.assertIn('@click="open = !open"', html)

    def test_data_attributes(self):
        """Test data- attributes"""
        md = """{% div data-test="value" data-other="123" %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('data-test="value"', html)
        self.assertIn('data-other="123"', html)

    def test_nested_tags(self):
        """Test nested Django-like tags"""
        md = """{% div .outer %}
{% div .inner #inner-id %}
Content
{% enddiv %}
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('<div class="outer">', html)
        self.assertIn('<div class="inner" id="inner-id">', html)

    def test_mixed_content(self):
        """Test mixing markdown with Django-like tags"""
        md = """{% div .container %}
# Heading
- List item 1
- List item 2
{% div .nested %}
**Bold text**
{% enddiv %}
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn('<div class="container">', html)
        self.assertIn('<h1>Heading</h1>', html)
        self.assertIn('<ul>', html)
        self.assertIn('<div class="nested">', html)
        self.assertIn('<strong>Bold text</strong>', html)

    def test_invalid_tags(self):
        """Test handling of mismatched tags"""
        md = """{% div .test %}
Content
{% endspan %}"""
        with self.assertRaises(ValueError):
            parser = MarkdownParser(md)
            parser.get_html()

    def test_tailwind_classes(self):
        """Test Tailwind CSS class combinations"""
        md = """{% div .p-4 .mx-auto .bg-gray-100 .hover:bg-gray-200 .dark:bg-gray-800 %}
Content
{% enddiv %}"""
        parser = MarkdownParser(md)
        html = parser.get_html()
        self.assertIn(
            'class="p-4 mx-auto bg-gray-100 hover:bg-gray-200 dark:bg-gray-800"', html)
