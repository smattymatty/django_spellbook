# tests/test_validate_command.py
"""
Unit tests for frontmatter validation functionality.

NOTE: These tests do NOT include wizard integration tests that call
call_command('spellbook_wizard') to avoid infinite loops during test execution.
Manual testing of the wizard UI should be performed separately.

To manually test the wizard:
1. Run: python manage.py spellbook_wizard
2. Select option 2 (Validate)
3. Select option 1 (Validate frontmatter)
4. Verify output shows validation results
"""

import tempfile
import shutil
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from django.test import TestCase

from django_spellbook.management.commands.wizard.validate import (
    FrontmatterValidator,
    ValidationError,
    DeadLinkFinder
)


class TestFrontmatterValidator(TestCase):
    """Test frontmatter validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.stdout = StringIO()
        self.validator = FrontmatterValidator(self.stdout, style_func=None)

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def _create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test markdown file."""
        filepath = Path(self.temp_dir) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_valid_frontmatter_passes(self):
        """Valid frontmatter should pass validation."""
        content = """---
title: Test Page
published: 2025-01-15
author: Test Author
tags:
  - test
  - guide
---

# Test Content
"""
        filepath = self._create_test_file('valid.md', content)
        errors = self.validator.validate_page(filepath)
        self.assertEqual(len(errors), 0)

    def test_missing_title_detected(self):
        """Missing title should be detected."""
        content = """---
published: 2025-01-15
author: Test Author
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('missing_title.md', content)
        errors = self.validator.validate_page(filepath)
        self.assertTrue(any(e.field == 'title' for e in errors))
        self.assertTrue(any('Missing: title' in e.message for e in errors))

    def test_missing_published_detected(self):
        """Missing published date should be detected."""
        content = """---
title: Test Page
author: Test Author
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('missing_published.md', content)
        errors = self.validator.validate_page(filepath)
        self.assertTrue(any(e.field == 'published' for e in errors))

    def test_missing_author_detected(self):
        """Missing author should be detected."""
        content = """---
title: Test Page
published: 2025-01-15
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('missing_author.md', content)
        errors = self.validator.validate_page(filepath)
        self.assertTrue(any(e.field == 'author' for e in errors))

    def test_missing_tags_detected(self):
        """Missing tags should be detected."""
        content = """---
title: Test Page
published: 2025-01-15
author: Test Author
---

# Test Content
"""
        filepath = self._create_test_file('missing_tags.md', content)
        errors = self.validator.validate_page(filepath)
        self.assertTrue(any(e.field == 'tags' for e in errors))

    def test_invalid_date_format_detected(self):
        """Invalid date format should be detected."""
        content = """---
title: Test Page
published: Dec 2025
author: Test Author
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('invalid_date.md', content)
        errors = self.validator.validate_page(filepath)
        date_errors = [e for e in errors if e.field == 'published']
        self.assertTrue(len(date_errors) > 0)
        self.assertTrue(any('invalid date format' in e.message for e in date_errors))

    def test_tags_as_string_detected(self):
        """Tags as string instead of list should be detected."""
        content = """---
title: Test Page
published: 2025-01-15
author: Test Author
tags: "guide, tutorial"
---

# Test Content
"""
        filepath = self._create_test_file('tags_string.md', content)
        errors = self.validator.validate_page(filepath)
        tag_errors = [e for e in errors if e.field == 'tags']
        self.assertTrue(len(tag_errors) > 0)
        self.assertTrue(any('must be a list' in e.message for e in tag_errors))

    def test_empty_tags_list_detected(self):
        """Empty tags list should be detected."""
        content = """---
title: Test Page
published: 2025-01-15
author: Test Author
tags: []
---

# Test Content
"""
        filepath = self._create_test_file('empty_tags.md', content)
        errors = self.validator.validate_page(filepath)
        tag_errors = [e for e in errors if e.field == 'tags']
        self.assertTrue(len(tag_errors) > 0)
        self.assertTrue(any('at least 1 item' in e.message for e in tag_errors))

    def test_empty_title_detected(self):
        """Empty title string should be detected."""
        content = """---
title: ""
published: 2025-01-15
author: Test Author
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('empty_title.md', content)
        errors = self.validator.validate_page(filepath)
        title_errors = [e for e in errors if e.field == 'title']
        self.assertTrue(len(title_errors) > 0)
        self.assertTrue(any('cannot be empty' in e.message for e in title_errors))

    def test_title_wrong_type_detected(self):
        """Title as non-string should be detected."""
        content = """---
title: 123
published: 2025-01-15
author: Test Author
tags:
  - test
---

# Test Content
"""
        filepath = self._create_test_file('title_wrong_type.md', content)
        errors = self.validator.validate_page(filepath)
        title_errors = [e for e in errors if e.field == 'title']
        self.assertTrue(len(title_errors) > 0)
        self.assertTrue(any('must be a string' in e.message for e in title_errors))

    def test_validate_all_returns_errors_by_file(self):
        """validate_all should return errors grouped by file."""
        # Create multiple files with different errors
        self._create_test_file('valid.md', """---
title: Valid
published: 2025-01-15
author: Test
tags:
  - test
---
Content""")

        self._create_test_file('invalid.md', """---
title: Invalid
published: bad-date
tags:
  - test
---
Content""")

        results = self.validator.validate_all(Path(self.temp_dir))

        # Should have 1 file with errors (invalid.md)
        self.assertEqual(len(results), 1)

        # Check that invalid.md is in results
        invalid_path = Path(self.temp_dir) / 'invalid.md'
        self.assertIn(invalid_path, results)

    @patch('builtins.input')
    def test_interactive_fix_skips_all(self, mock_input):
        """Interactive fix with all skips should not modify file."""
        content = """---
published: 2025-01-15
tags:
  - test
---
Content"""
        filepath = self._create_test_file('test.md', content)

        # Simulate user skipping all fixes
        mock_input.side_effect = ['skip', 'skip']

        errors = [
            ValidationError(field='title', message='Missing: title'),
            ValidationError(field='author', message='Missing: author')
        ]

        modified = self.validator.fix_interactive(filepath, errors)

        self.assertFalse(modified)

    @patch('builtins.input')
    def test_interactive_fix_adds_fields(self, mock_input):
        """Interactive fix should add missing fields."""
        content = """---
published: 2025-01-15
tags:
  - test
---
Content"""
        filepath = self._create_test_file('test.md', content)

        # Simulate user entering values
        mock_input.side_effect = ['My Title', 'John Doe']

        errors = [
            ValidationError(field='title', message='Missing: title'),
            ValidationError(field='author', message='Missing: author')
        ]

        modified = self.validator.fix_interactive(filepath, errors)

        self.assertTrue(modified)

        # Read file and check it was updated
        with open(filepath, 'r') as f:
            updated_content = f.read()

        self.assertIn('title: My Title', updated_content)
        self.assertIn('author: John Doe', updated_content)

    @patch('builtins.input')
    def test_interactive_fix_date_with_today(self, mock_input):
        """Interactive fix should accept 'today' for date."""
        content = """---
title: Test
author: Test
tags:
  - test
---
Content"""
        filepath = self._create_test_file('test.md', content)

        # Simulate user entering 'today'
        mock_input.return_value = 'today'

        errors = [
            ValidationError(field='published', message='Missing: published')
        ]

        modified = self.validator.fix_interactive(filepath, errors)

        self.assertTrue(modified)

        # Read file and check date was added
        with open(filepath, 'r') as f:
            updated_content = f.read()

        # Should contain today's date in YYYY-MM-DD format (may have quotes from YAML)
        today = datetime.now().strftime('%Y-%m-%d')
        self.assertTrue(
            f'published: {today}' in updated_content or f"published: '{today}'" in updated_content,
            f"Expected published date {today} not found in content"
        )

    @patch('builtins.input')
    def test_interactive_fix_tags_comma_separated(self, mock_input):
        """Interactive fix should parse comma-separated tags."""
        content = """---
title: Test
published: 2025-01-15
author: Test
---
Content"""
        filepath = self._create_test_file('test.md', content)

        # Simulate user entering comma-separated tags
        mock_input.return_value = 'guide, tutorial, python'

        errors = [
            ValidationError(field='tags', message='Missing: tags')
        ]

        modified = self.validator.fix_interactive(filepath, errors)

        self.assertTrue(modified)

        # Read file and check tags were added
        with open(filepath, 'r') as f:
            updated_content = f.read()

        self.assertIn('tags:', updated_content)
        self.assertIn('- guide', updated_content)
        self.assertIn('- tutorial', updated_content)
        self.assertIn('- python', updated_content)


class TestDeadLinkFinder(TestCase):
    """Test dead link detection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.stdout = StringIO()
        self.finder = DeadLinkFinder(self.stdout, style_func=None)

    def test_find_dead_links_placeholder(self):
        """Dead link finder should return placeholder for now."""
        # Since dead link detection is not fully implemented yet,
        # just test that it returns empty dict
        result = self.finder.find_dead_links([Path('/tmp')])
        self.assertEqual(result, {})


class TestValidateMenuIntegration(TestCase):
    """Test validate menu integration with wizard."""

    def test_frontmatter_validator_exists(self):
        """FrontmatterValidator class should be importable."""
        from django_spellbook.management.commands.wizard.validate import FrontmatterValidator
        self.assertIsNotNone(FrontmatterValidator)

    def test_dead_link_finder_exists(self):
        """DeadLinkFinder class should be importable."""
        from django_spellbook.management.commands.wizard.validate import DeadLinkFinder
        self.assertIsNotNone(DeadLinkFinder)

    def test_validate_menu_handler_exists(self):
        """Validate menu handler should be importable."""
        from django_spellbook.management.commands.wizard.validate import handle_validate_menu
        self.assertIsNotNone(handle_validate_menu)


class TestSpellbookValidateCommand(TestCase):
    """Test the standalone spellbook_validate management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.stdout = StringIO()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def _create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test markdown file."""
        filepath = Path(self.temp_dir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_command_exists(self):
        """spellbook_validate command should be importable."""
        from django_spellbook.management.commands.spellbook_validate import Command
        cmd = Command()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.help, 'Validate frontmatter in markdown files')

    def test_command_has_fix_argument(self):
        """Command should have --fix argument."""
        from django_spellbook.management.commands.spellbook_validate import Command
        cmd = Command()
        parser = cmd.create_parser('manage.py', 'spellbook_validate')

        # Check if --fix argument exists
        fix_action = None
        for action in parser._actions:
            if '--fix' in action.option_strings:
                fix_action = action
                break

        self.assertIsNotNone(fix_action)
        self.assertEqual(fix_action.dest, 'fix')

    def test_command_has_source_path_argument(self):
        """Command should have --source-path argument."""
        from django_spellbook.management.commands.spellbook_validate import Command
        cmd = Command()
        parser = cmd.create_parser('manage.py', 'spellbook_validate')

        # Check if --source-path argument exists
        source_path_action = None
        for action in parser._actions:
            if '--source-path' in action.option_strings:
                source_path_action = action
                break

        self.assertIsNotNone(source_path_action)
        self.assertEqual(source_path_action.dest, 'source_path')

    def test_audit_mode_reports_errors(self):
        """Audit mode should report errors without modifying files."""
        # Create a file with missing frontmatter
        self._create_test_file('invalid.md', """---
title: Test
published: 2025-01-15
---
Content""")

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, stdout=out)

        output = out.getvalue()
        # Should report missing fields
        self.assertIn('invalid.md', output)
        self.assertIn('Missing: author', output)
        self.assertIn('Missing: tags', output)
        # Should suggest using --fix
        self.assertIn('--fix', output)

    def test_audit_mode_does_not_modify_files(self):
        """Audit mode should not modify files."""
        filepath = self._create_test_file('test.md', """---
title: Test
---
Content""")

        # Read original content
        with open(filepath, 'r') as f:
            original_content = f.read()

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, stdout=out)

        # Read content after validation
        with open(filepath, 'r') as f:
            after_content = f.read()

        # Content should be unchanged
        self.assertEqual(original_content, after_content)

    def test_valid_files_pass_validation(self):
        """Files with valid frontmatter should pass."""
        self._create_test_file('valid.md', """---
title: Valid Page
published: 2025-01-15
author: Test Author
tags:
  - test
  - valid
---
Content""")

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, stdout=out)

        output = out.getvalue()
        # Should report success
        self.assertIn('valid', output.lower())
        self.assertTrue('1 pages valid' in output or 'All 1 pages valid' in output)

    @patch('builtins.input')
    def test_fix_mode_modifies_files(self, mock_input):
        """Fix mode should modify files when user provides input."""
        filepath = self._create_test_file('fixable.md', """---
published: 2025-01-15
tags:
  - test
---
Content""")

        # Mock user input: provide title and author
        mock_input.side_effect = ['My Title', 'John Doe']

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, '--fix', stdout=out)

        # Read modified content
        with open(filepath, 'r') as f:
            modified_content = f.read()

        # Should have added the fields
        self.assertIn('title: My Title', modified_content)
        self.assertIn('author: John Doe', modified_content)

    @patch('builtins.input')
    def test_fix_mode_skip_behavior(self, mock_input):
        """Fix mode should skip files when user chooses skip."""
        filepath = self._create_test_file('skippable.md', """---
published: 2025-01-15
tags:
  - test
---
Content""")

        # Read original content
        with open(filepath, 'r') as f:
            original_content = f.read()

        # Mock user input: skip everything
        mock_input.side_effect = ['skip', 'skip']

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, '--fix', stdout=out)

        # Read content after command
        with open(filepath, 'r') as f:
            after_content = f.read()

        # Content should be unchanged
        self.assertEqual(original_content, after_content)

        # Output should mention skipped
        output = out.getvalue()
        self.assertTrue('Skipped' in output or 'skip' in output.lower())

    def test_source_path_override(self):
        """--source-path should override settings."""
        self._create_test_file('custom.md', """---
title: Test
---
Content""")

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, stdout=out)

        output = out.getvalue()
        # Should mention using the custom source path
        self.assertTrue('Using source path' in output or self.temp_dir in output)
        # Should find the file
        self.assertIn('custom.md', output)

    def test_multiple_files_validation(self):
        """Should validate multiple files and report correctly."""
        # Create multiple files with different issues
        self._create_test_file('valid.md', """---
title: Valid
published: 2025-01-15
author: Test
tags:
  - test
---
Content""")

        self._create_test_file('invalid1.md', """---
title: Invalid 1
---
Content""")

        self._create_test_file('invalid2.md', """---
published: 2025-01-15
author: Test
---
Content""")

        from django.core.management import call_command
        out = StringIO()

        call_command('spellbook_validate', '--source-path', self.temp_dir, stdout=out)

        output = out.getvalue()
        # Should report 2 invalid files
        self.assertTrue('2 pages with issues' in output or '2 pages' in output)
        # Should report 1 valid file
        self.assertTrue('1 pages valid' in output or '1 page valid' in output)
        # Should mention both invalid files
        self.assertIn('invalid1.md', output)
        self.assertIn('invalid2.md', output)
