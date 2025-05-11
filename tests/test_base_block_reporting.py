import unittest
from unittest.mock import Mock, patch
from io import StringIO

from django_spellbook.blocks import BasicSpellBlock
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

class TestBasicSpellBlockReporting(unittest.TestCase):
    """Test cases for the BasicSpellBlock class reporting functionality"""

    def setUp(self):
        """Set up test environment"""
        self.reporter = MarkdownReporter(StringIO())
        
        # Create a concrete implementation of BasicSpellBlock for testing
        class TestBlock(BasicSpellBlock):
            name = "test_block"
            template = "test_template.html"
            
            # Override render method to avoid template loading
            def render(self):
                context = self.get_context()
                if self.reporter:
                    self.reporter.record_spellblock_usage(self.name, success=True)
                return "<div>rendered content</div>"
            
        self.TestBlockClass = TestBlock
        
        # Mock the MarkdownParser
        self.parser_patch = patch('django_spellbook.markdown.parser.MarkdownParser')
        self.mock_parser_class = self.parser_patch.start()
        self.mock_parser = Mock()
        self.mock_parser_class.return_value = self.mock_parser
        self.mock_parser.get_html.return_value = "<p>processed content</p>"

    def tearDown(self):
        """Clean up patches"""
        self.parser_patch.stop()

    def test_reporter_passed_to_init(self):
        """Test that reporter is stored when passed to __init__"""
        block = self.TestBlockClass(content="test content", reporter=self.reporter)
        self.assertEqual(block.reporter, self.reporter)

    def test_reporter_usage_recorded_on_successful_render(self):
        """Test that successful block rendering is recorded with the reporter"""
        block = self.TestBlockClass(content="test content", reporter=self.reporter)
        
        # Call render and verify it returns expected content
        result = block.render()
        self.assertEqual(result, "<div>rendered content</div>")
        

    def test_reporter_not_called_when_not_provided(self):
        """Test that reporter methods aren't called when no reporter is provided"""
        block = self.TestBlockClass(content="test content", reporter=None)
        
        # Call render
        result = block.render()
        
        # Verify that it works without a reporter
        self.assertEqual(result, "<div>rendered content</div>")

    def test_process_content_with_reporter(self):
        """Test that process_content creates a MarkdownParser with the reporter"""
        # Create a concrete instance with a mock reporter
        block = self.TestBlockClass(content="test content", reporter=self.reporter)
        
        # Create a separate patch for this test to check parameters
        with patch('django_spellbook.markdown.engine.SpellbookMarkdownEngine') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.get_html.return_value = "<p>processed content</p>"
            
            # Call process_content
            result = block.process_content()
            
            

    def test_real_reporter_integration(self):
        """Integration test with a real MarkdownReporter"""
        # Create a real reporter instance
        stdout = StringIO()
        real_reporter = MarkdownReporter(stdout=stdout)
        
        # Create a block with the real reporter
        block = self.TestBlockClass(content="test content", reporter=real_reporter)
        
        # Call render (twice to simulate the first as initialization)
        block.render()
        block.render()
        
        
        # Check if the spellblock was recorded
        # This assumes you've implemented spellblocks attribute in MarkdownReporter
        found = False
        for recorded_block in real_reporter.spellblocks:
            if recorded_block.name == "test_block":
                found = True
                self.assertEqual(recorded_block.total_uses, 2)
                self.assertEqual(recorded_block.failed_uses, 0)
        
        self.assertTrue(found, "Block wasn't recorded in the reporter")

    def test_multiple_renders_increment_counter(self):
        """Test that multiple renders of the same block increment the counter"""
        # Create a real reporter instance
        stdout = StringIO()
        real_reporter = MarkdownReporter(stdout=stdout)
        
        # Create a block with the real reporter
        block = self.TestBlockClass(content="test content", reporter=real_reporter)
        
        # Call render multiple times (an extra render is called by the test)
        block.render()
        block.render()
        block.render()
        block.render()
        
        # Check if the spellblock counter was incremented
        for recorded_block in real_reporter.spellblocks:
            if recorded_block.name == "test_block":
                self.assertEqual(recorded_block.total_uses, 4)
                break
        else:
            self.fail("Block wasn't recorded in the reporter")
                
    def test_actual_render_method_with_mocked_template_engine(self):
        """Test the actual render method by mocking the template engine"""
        # Create a subclass that doesn't override render
        class StandardBlock(BasicSpellBlock):
            name = "standard_block"
            template = "standard_template.html"
        
        # More comprehensive template engine mocking
        template_mock = Mock()
        template_mock.render.return_value = "<div>mocked content</div>"
        
        with patch('django.template.loader.get_template', return_value=template_mock) as mock_get_template:
            # Create a block with the reporter
            block = StandardBlock(content="test content", reporter=self.reporter)
            
            # Call the original render method
            result = block.render()
            
            # Verify it called get_template
            mock_get_template.assert_called_once_with("standard_template.html", using=None)
            
            # Verify the result
            self.assertEqual(result, "<div>mocked content</div>")
            
