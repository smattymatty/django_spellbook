import os
import json
import tempfile
from io import StringIO
from unittest import TestCase, mock
from django.core.management.color import no_style
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

class MarkdownReporterTestCase(TestCase):
    """Tests for the MarkdownReporter class with various reporting arguments."""

    def setUp(self):
        """Set up test environment."""
        self.stdout = StringIO()  # Capture output for testing
        self.sample_results = [
            # (md_path, content_app, url_prefix, success, processed_count)
            ('/path/to/source1', 'app1', 'docs', True, 5),
            ('/path/to/source2', 'app2', 'blog', False, 0),
            ('/path/to/source3', 'app3', '', True, 3),
        ]

    def tearDown(self):
        """Clean up after tests."""
        self.stdout.close()

    def test_default_initialization(self):
        """Test that reporter initializes with default values."""
        reporter = MarkdownReporter(self.stdout)
        self.assertEqual(reporter.report_level, 'detailed')
        self.assertEqual(reporter.report_format, 'text')
        self.assertIsNone(reporter.report_output)

    def test_custom_initialization(self):
        """Test that reporter initializes with custom values."""
        reporter = MarkdownReporter(
            self.stdout, 
            report_level='minimal', 
            report_format='json', 
            report_output='test.json'
        )
        self.assertEqual(reporter.report_level, 'minimal')
        self.assertEqual(reporter.report_format, 'json')
        self.assertEqual(reporter.report_output, 'test.json')

    def test_should_output_method(self):
        """Test the _should_output method for different report levels."""
        # Minimal level
        reporter = MarkdownReporter(self.stdout, report_level='minimal')
        self.assertTrue(reporter._should_output('minimal'))
        self.assertFalse(reporter._should_output('detailed'))
        self.assertFalse(reporter._should_output('debug'))
        
        # Detailed level
        reporter = MarkdownReporter(self.stdout, report_level='detailed')
        self.assertTrue(reporter._should_output('minimal'))
        self.assertTrue(reporter._should_output('detailed'))
        self.assertFalse(reporter._should_output('debug'))
        
        # Debug level
        reporter = MarkdownReporter(self.stdout, report_level='debug')
        self.assertTrue(reporter._should_output('minimal'))
        self.assertTrue(reporter._should_output('detailed'))
        self.assertTrue(reporter._should_output('debug'))
        
        # None format should never output
        reporter = MarkdownReporter(self.stdout, report_format='none')
        self.assertFalse(reporter._should_output('minimal'))
        self.assertFalse(reporter._should_output('detailed'))
        self.assertFalse(reporter._should_output('debug'))

    def test_report_level_minimal(self):
        """Test minimal report level output."""
        reporter = MarkdownReporter(self.stdout, report_level='minimal', style=no_style())
        
        # These should not output with minimal level
        reporter.write("Detailed message", level='detailed')
        reporter.success("Detailed success", level='detailed')
        reporter.warning("Detailed warning", level='detailed')
        
        # These should output with minimal level
        reporter.write("Minimal message", level='minimal')
        reporter.success("Minimal success", level='minimal')
        reporter.warning("Minimal warning", level='minimal')
        reporter.error("Error message")  # Errors always show
        
        output = self.stdout.getvalue()
        self.assertNotIn("Detailed message", output)
        self.assertNotIn("Detailed success", output)
        self.assertNotIn("Detailed warning", output)
        self.assertIn("Minimal message", output)
        self.assertIn("Minimal success", output)
        self.assertIn("Minimal warning", output)
        self.assertIn("Error message", output)

    def test_report_level_detailed(self):
        """Test detailed report level output."""
        reporter = MarkdownReporter(self.stdout, report_level='detailed', style=no_style())
        
        # These should output with detailed level
        reporter.write("Detailed message", level='detailed')
        reporter.success("Detailed success", level='detailed')
        reporter.warning("Detailed warning", level='detailed')
        reporter.write("Minimal message", level='minimal')
        
        # These should not output with detailed level
        reporter.write("Debug message", level='debug')
        
        output = self.stdout.getvalue()
        self.assertIn("Detailed message", output)
        self.assertIn("Detailed success", output)
        self.assertIn("Detailed warning", output)
        self.assertIn("Minimal message", output)
        self.assertNotIn("Debug message", output)

    def test_report_level_debug(self):
        """Test debug report level output."""
        reporter = MarkdownReporter(self.stdout, report_level='debug', style=no_style())
        
        # All messages should output with debug level
        reporter.write("Debug message", level='debug')
        reporter.write("Detailed message", level='detailed')
        reporter.write("Minimal message", level='minimal')
        
        output = self.stdout.getvalue()
        self.assertIn("Debug message", output)
        self.assertIn("Detailed message", output)
        self.assertIn("Minimal message", output)

    def test_report_format_none(self):
        """Test that 'none' format suppresses all output."""
        reporter = MarkdownReporter(self.stdout, report_format='none', style=no_style())
        
        reporter.write("Test message")
        reporter.success("Success message")
        reporter.warning("Warning message")
        reporter.error("Error message")
        reporter.generate_summary_report(self.sample_results)
        
        output = self.stdout.getvalue()
        self.assertEqual("", output)  # No output should be produced

    def test_text_report_format(self):
        """Test the text report format."""
        reporter = MarkdownReporter(self.stdout, report_format='text', style=no_style())
        reporter.generate_summary_report(self.sample_results)
        
        output = self.stdout.getvalue()
        self.assertIn("Processing Summary", output)
        self.assertIn("2 of 3 pairs processed successfully", output)
        self.assertIn("Total files processed: 8", output)
        self.assertIn("Failed pairs", output)
        self.assertIn("app2", output)

    def test_json_report_format(self):
        """Test the JSON report format."""
        reporter = MarkdownReporter(self.stdout, report_format='json', style=no_style())
        reporter.generate_summary_report(self.sample_results)
        
        output = self.stdout.getvalue()
        # Verify it's valid JSON
        json_data = json.loads(output)
        
        # Check the content
        self.assertEqual(json_data["summary"]["total_pairs"], 3)
        self.assertEqual(json_data["summary"]["successful_pairs"], 2)
        self.assertEqual(json_data["summary"]["total_processed_files"], 8)
        self.assertEqual(len(json_data["pairs"]), 3)
        self.assertEqual(len(json_data["failed_pairs"]), 1)
        self.assertEqual(json_data["failed_pairs"][0]["destination"], "app2")

    def test_report_output_to_file(self):
        """Test output to a file."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Initialize reporter with output file
            reporter = MarkdownReporter(
                self.stdout, 
                report_format='text', 
                report_output=temp_path, 
                style=no_style()
            )
            
            reporter.generate_summary_report(self.sample_results)
            
            # Close file to ensure content is written
            if hasattr(reporter, 'output_file') and reporter.output_file:
                reporter.output_file.close()
            
            # Read the file content
            with open(temp_path, 'r') as f:
                file_content = f.read()
            
            # Check that output was written to file
            self.assertIn("Processing Summary", file_content)
            self.assertIn("2 of 3 pairs processed successfully", file_content)
            
            # Verify stdout is empty (redirected to file)
            self.assertEqual("", self.stdout.getvalue())
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_report_output_file_error(self):
        """Test handling of errors when opening output file."""
        # Use a directory path which will cause a permission error when trying to open as a file
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = MarkdownReporter(
                self.stdout, 
                report_format='text', 
                report_output=temp_dir,  # Directory, not a file
                style=no_style()
            )
            
            # Should fall back to stdout
            reporter.generate_summary_report(self.sample_results)
            
            output = self.stdout.getvalue()
            self.assertIn("Error opening output file", output)
            self.assertIn("Processing Summary", output)

    def test_combined_options(self):
        """Test combination of different options."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Test JSON format with minimal level to file
            reporter = MarkdownReporter(
                self.stdout, 
                report_level='minimal',
                report_format='json', 
                report_output=temp_path, 
                style=no_style()
            )
            
            # Should not output these with minimal level
            reporter.write("Detailed info", level='detailed')
            
            # Should still generate report
            reporter.generate_summary_report(self.sample_results)
            
            # Close file to ensure content is written
            if hasattr(reporter, 'output_file') and reporter.output_file:
                reporter.output_file.close()
            
            # Stdout should be empty
            self.assertEqual("", self.stdout.getvalue())
            
            # File should contain valid JSON
            with open(temp_path, 'r') as f:
                file_content = f.read()
            
            json_data = json.loads(file_content)
            self.assertEqual(json_data["summary"]["total_pairs"], 3)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
                
class MarkdownReporterSpellblockTestCase(TestCase):
    """Tests for the MarkdownReporter class with spellblock usage tracking."""
    
    def setUp(self):
        """Set up test environment."""
        self.stdout = StringIO()  # Capture output for testing
        self.sample_results = [
            # (md_path, content_app, url_prefix, success, processed_count)
            ('/path/to/source1', 'app1', 'docs', True, 5),
            ('/path/to/source2', 'app2', 'blog', False, 0),
            ('/path/to/source3', 'app3', '', True, 3),
        ]
        
        # Create a reporter with a sample list of spellblocks
        from django_spellbook.management.commands.spellbook_md_p.discovery import SpellblockStatistics
        self.reporter = MarkdownReporter(
            self.stdout, 
            report_level='minimal', 
            report_format='json', 
            report_output='test.json',
        )
        self.reporter.spellblocks = [
            SpellblockStatistics('block1', 10, 0),
            SpellblockStatistics('block2', 20, 0),
            SpellblockStatistics('block3', 30, 0),
            
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.stdout.close()
    
    def test_record_spellblock_usage(self):
        """Test that spellblock usage is recorded correctly."""
        # Test with a block that's not in the list
        self.reporter.record_spellblock_usage('block4')
        
        # Verify the list was extended with a new block
        self.assertEqual(len(self.reporter.spellblocks), 4)
        self.assertEqual(self.reporter.spellblocks[3].name, 'block4')
        self.assertEqual(self.reporter.spellblocks[3].total_uses, 0)

        
        # Test with a block that's already in the list
        self.reporter.record_spellblock_usage('block1')
        
        # Verify the existing block was updated
        self.assertEqual(self.reporter.spellblocks[0].total_uses, 11)
        
        self.reporter.record_spellblock_usage('block2', success=False)
        
        # Verify the existing block was updated
        self.assertEqual(self.reporter.spellblocks[1].failed_uses, 1)
        
    def test_generate_text_report_with_failing_spellblocks(self):
        """Test that the text report includes spellblock usage information."""
        # Test with a failing spellblock
        self.reporter.record_spellblock_usage('block1')
        self.reporter.record_spellblock_usage('block3', success=False)
        self.reporter.record_spellblock_usage('block4', success=False)
        
        # Call the function
        message = self.reporter._generate_text_report(
            self.sample_results, 
            success_count=3, 
            total_processed=10, 
            failed_pairs=[]
        )
        
        # Verify the returned message includes the spellblock usage
        self.assertIn("block3", message)
        
    def test_generate_json_report_with_failing_spellblocks(self):
        """Test that the JSON report includes spellblock usage information."""
        # Test with a failing spellblock
        self.reporter.record_spellblock_usage('block1')
        self.reporter.record_spellblock_usage('block3', success=False)
        self.reporter.record_spellblock_usage('block4', success=False)
        
        # Call the function
        json_dict = self.reporter._generate_json_report(
            self.sample_results, 
            success_count=3, 
            total_processed=10, 
            failed_pairs=[]
        )
        
        # Verify the returned message includes the spellblock usage
        # report_data["spellblocks"] is a list of dictionaries
        #self.assertIn({"name": "block3", "total_files": 30, "successful_files": 25, "failed_files": 6}, json_dict["spellblocks"])
        #self.assertIn({"name": "block4", "total_files": 0, "successful_files": 0, "failed_files": 0}, json_dict["spellblocks"])

        self.assertIn({'name': 'block3', 'total_uses': 30, 'failed_uses': 1}, json_dict["spellblocks"])
        self.assertIn({'name': 'block4', 'total_uses': 0, 'failed_uses': 0}, json_dict["spellblocks"])