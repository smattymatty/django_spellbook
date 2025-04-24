from io import StringIO
from unittest import TestCase
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

class MarkdownReporterTests(TestCase):
    """Tests for the MarkdownReporter class"""
    
    def setUp(self):
        """Set up test environment"""
        self.output = StringIO()
        self.styled_output = OutputWrapper(self.output)
        self.styled_output.style = color_style()
    
    def test_summary_report_all_successful(self):
        """Test summary report when all pairs are successful"""
        # Create reporter with Django-style output
        reporter = MarkdownReporter(self.styled_output)
        
        # Mock results with all successful pairs
        pair_results = [
            ('/path1', 'app1', 'prefix1', True, 5),  # 5 files processed successfully
            ('/path2', 'app2', 'prefix2', True, 3),  # 3 files processed successfully
        ]
        
        # Generate report
        reporter.generate_summary_report(pair_results)
        
        # Verify output content (not exact string matching)
        output_text = self.output.getvalue()
        self.assertIn("Processing Summary", output_text)
        self.assertIn("All 2 source-destination pairs processed successfully", output_text)
        self.assertIn("Total files processed: 8", output_text)  # 5 + 3 = 8
    
    def test_summary_report_with_failures(self):
        """Test summary report when some pairs fail"""
        # Create reporter with Django-style output
        reporter = MarkdownReporter(self.styled_output)
        
        # Mock results with one successful and one failed pair
        pair_results = [
            ('/path1', 'app1', 'prefix1', True, 5),   # 5 files processed successfully
            ('/path2', 'app2', 'prefix2', False, 0),  # Failed processing
        ]
        
        # Generate report
        reporter.generate_summary_report(pair_results)
        
        # Verify output content (not exact string matching)
        output_text = self.output.getvalue()
        self.assertIn("Processing Summary", output_text)
        self.assertIn("1 of 2 pairs processed successfully", output_text)
        self.assertIn("Total files processed: 5", output_text)
        self.assertIn("/path2", output_text)  # Failed path should be mentioned
        self.assertIn("app2", output_text)    # Failed app should be mentioned
    
    def test_summary_report_with_plain_io(self):
        """Test that reporter works with plain StringIO (no style attribute)"""
        # Create reporter with plain StringIO (no style)
        plain_output = StringIO()
        reporter = MarkdownReporter(plain_output)
        
        # Mock results
        pair_results = [
            ('/path1', 'app1', 'prefix1', True, 5),
        ]
        
        # This should not raise an AttributeError
        reporter.generate_summary_report(pair_results)
        
        # Verify basic output was generated
        output_text = plain_output.getvalue()
        self.assertIn("Processing Summary", output_text)
        self.assertIn("processed successfully", output_text)