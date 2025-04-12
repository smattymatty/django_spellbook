from django.test import TestCase

from django_spellbook.utils import remove_leading_dash, titlefy


class TestUtils(TestCase):
    def test_remove_leading_dash(self):
        """Test removing leading dashes from a string"""
        result = remove_leading_dash('--test')
        self.assertEqual(result, 'test')

    def test_titlefy(self):
        """Test titlefy function"""
        result = titlefy('test-page')
        self.assertEqual(result, 'Test Page')
        result = titlefy('this-is-a-test-page')
        self.assertEqual(result, 'This is a Test Page')

    def test_titlefy_without_dashes(self):
        """Test titlefy function without dashes"""
        result = titlefy('test page')
        self.assertEqual(result, 'Test Page')
