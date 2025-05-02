import unittest
from django_spellbook.markdown.content_metrics import get_word_count, get_reading_time_minutes

class TestContentMetrics(unittest.TestCase):
    def test_get_word_count_empty_string(self):
        self.assertEqual(get_word_count(''), 0)
    
    def test_get_word_count(self):
        self.assertEqual(get_word_count('This is a test'), 4)
        self.assertEqual(get_word_count('This is a test.'), 4)
        self.assertEqual(get_word_count('This is a test. This is another test.'), 8)

    def test_get_reading_time_minutes(self):
        self.assertEqual(get_reading_time_minutes('This is a test'), 1)
        self.assertEqual(get_reading_time_minutes(
            """
            Wumbo, This is a test.
            """*100), 2)
        
    def test_get_word_count_with_spellblock(self):
        self.assertEqual(get_word_count(
            '''
            {~ accordion title="Test" ~}
            This is a test.
            {~ accordion ~}
            '''), 4)
        
        self.assertEqual(get_word_count(
            '''
            {~ card title="Test" footer="Footer" ~}
            This is a test.
            {~ card ~}
            '''), 4)
        
    def test_get_word_count_with_django_tags(self):
        self.assertEqual(get_word_count(
            '''
            {% div %}
            This is a test.
            {% enddiv %}
            '''), 4)
        
        self.assertEqual(get_word_count(
            '''
            {% div %}
            This is a test.
            {% enddiv %}
            {% div %}
            Another test.
            {% enddiv %}
            '''), 6)
