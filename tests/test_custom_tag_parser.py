import unittest
from unittest.mock import Mock, patch
import io
import re
from typing import List

# Classes/functions/exception from the module being tested
from django_spellbook.markdown.extensions.custom_tag_parser import (
    process_nested_content,
    find_next_tag_in_chunk,
    handle_nested_start_tag,
    handle_nested_end_tag,
    NestedTagError # Import the specific exception
)
# Dependent classes from tag_stats
from django_spellbook.markdown.extensions.tag_stats import (
    FoundTagInfo, NestedContentResult, TagProcessingState
)

# --- Test Helper Functions ---

# Create real compiled regexes once for use in tests
RE_START_TEST = re.compile(r'{%\s*(\w+)([\s\S]*?)%}')
RE_END_TEST = re.compile(r'{%\s*end(\w+)\s*%}')

def create_mock_processor():
    """Creates a mock processor with compiled regex attributes."""
    mock_processor = Mock()
    mock_processor.RE_START = RE_START_TEST
    mock_processor.RE_END = RE_END_TEST
    # Add other attributes like parser if needed by functions being tested
    # mock_processor.parser = Mock()
    return mock_processor

# --- Test Classes ---

class TestFindNextTagInChunk(unittest.TestCase):
    """Tests the find_next_tag_in_chunk helper function."""

    def setUp(self):
        """Create a mock processor for each test."""
        self.mock_processor = create_mock_processor()

    def test_find_start_tag_only(self):
        content = "Some text {% starttag attrs %} more text"
        tag_info = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertTrue(tag_info.is_start_tag)
        self.assertIsNotNone(tag_info.match)
        self.assertEqual(tag_info.tag_name, "starttag")
        self.assertEqual(tag_info.full_tag_text, "{% starttag attrs %}")

    def test_find_end_tag_only(self):
        content = "Some text {% endtag %} more text"
        tag_info = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertFalse(tag_info.is_start_tag)
        self.assertIsNotNone(tag_info.match)
        self.assertEqual(tag_info.tag_name, "tag") # RE_END captures 'tag' from 'endtag'
        self.assertEqual(tag_info.full_tag_text, "{% endtag %}")

    def test_find_start_before_end(self):
        content = "Text {% start %} middle {% endstart %} end"
        tag_info = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertTrue(tag_info.is_start_tag)
        self.assertEqual(tag_info.tag_name, "start")

    def test_find_end_before_start(self):
        content = "Text {% endstart %} middle {% start %} end"
        tag_info = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertFalse(tag_info.is_start_tag)
        self.assertEqual(tag_info.tag_name, "start") # RE_END captures 'start'

    def test_no_tags_found(self):
        content = "Some text without any tags"
        tag_info = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertIsNone(tag_info.match)
        self.assertFalse(tag_info.is_start_tag)
        self.assertIsNone(tag_info.tag_name)
        self.assertIsNone(tag_info.full_tag_text)

    def test_find_from_position(self):
        content = "Before {% first %} Middle {% second %} After"
        # Find first tag
        tag_info1 = find_next_tag_in_chunk(self.mock_processor, content, 0)
        self.assertEqual(tag_info1.tag_name, "first")
        # Find second tag starting search *after* the first one
        tag_info2 = find_next_tag_in_chunk(self.mock_processor, content, tag_info1.match.end())
        self.assertEqual(tag_info2.tag_name, "second")


class TestHandleNestedStartTag(unittest.TestCase):
    """Tests the handle_nested_start_tag helper function."""

    def test_increments_level_and_appends_valid_start_tag(self):
        state = TagProcessingState("initial", [])
        state.nested_level = 1 # Start at level 1
        # Simulate a FoundTagInfo for a start tag
        match = RE_START_TEST.search("{% div class='foo' %}")
        tag_info = FoundTagInfo(match, True, "div", "{% div class='foo' %}")

        handle_nested_start_tag(tag_info, state)

        self.assertEqual(state.nested_level, 2) # Level incremented
        self.assertEqual(state.collected_parts, ["{% div class='foo' %}"]) # Tag added

    def test_ignores_start_tag_named_end(self):
        """Should ignore tags like {% endcustom %} if accidentally matched by RE_START."""
        state = TagProcessingState("initial", [])
        state.nested_level = 1
        match = RE_START_TEST.search("{% enddiv %}") # RE_START *can* match this
        tag_info = FoundTagInfo(match, True, "enddiv", "{% enddiv %}") # is_start=True, name starts with 'end'

        handle_nested_start_tag(tag_info, state)

        self.assertEqual(state.nested_level, 1) # Level NOT incremented
        self.assertEqual(state.collected_parts, []) # Tag NOT added


class TestHandleNestedEndTag(unittest.TestCase):
    """Tests the handle_nested_end_tag helper function."""

    def test_matching_end_tag_at_base_level(self):
        """Correct end tag found when nested_level is 1."""
        state = TagProcessingState("{% enddiv %} remaining", [])
        state.nested_level = 1
        match = RE_END_TEST.search(state.current_chunk)
        tag_info = FoundTagInfo(match, False, "div", "{% enddiv %}")
        target_tag = "div"

        should_stop = handle_nested_end_tag(tag_info, target_tag, state)

        self.assertTrue(should_stop) # Should signal to stop processing
        self.assertEqual(state.nested_level, 0) # Level decremented
        self.assertTrue(state.found_matching_end_tag) # Success flag set
        self.assertEqual(state.collected_parts, []) # End tag itself not added
        self.assertEqual(state.remaining_blocks, ["{% enddiv %} remaining"]) # Content after tag preserved

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mismatched_end_tag_at_base_level(self, mock_stdout):
        """Incorrect end tag found when nested_level is 1."""
        state = TagProcessingState("{% endspan %} remaining", [])
        state.nested_level = 1
        match = RE_END_TEST.search(state.current_chunk)
        tag_info = FoundTagInfo(match, False, "span", "{% endspan %}")
        target_tag = "div" # Expecting {% enddiv %}

        should_stop = handle_nested_end_tag(tag_info, target_tag, state)

        self.assertFalse(should_stop) # Should signal to continue processing
        self.assertEqual(state.nested_level, 0) # Level decremented
        self.assertFalse(state.found_matching_end_tag) # Success flag NOT set
        self.assertIn("Warning: Found mismatched end tag", mock_stdout.getvalue()) # Warning printed
        self.assertEqual(state.collected_parts, []) # Mismatched tag not added

    def test_end_tag_closing_nested_level(self):
        """End tag found when nested_level > 1."""
        state = TagProcessingState("{% endspan %}", [])
        state.nested_level = 2 # Inside a nested tag
        match = RE_END_TEST.search(state.current_chunk)
        tag_info = FoundTagInfo(match, False, "span", "{% endspan %}")
        target_tag = "div" # Outer tag we are searching for

        should_stop = handle_nested_end_tag(tag_info, target_tag, state)

        self.assertFalse(should_stop) # Should signal to continue processing
        self.assertEqual(state.nested_level, 1) # Level decremented
        self.assertFalse(state.found_matching_end_tag) # Outer tag not found yet
        self.assertEqual(state.collected_parts, ["{% endspan %}"]) # Inner end tag added

    def test_unbalanced_end_tag_raises_error(self):
        """NestedTagError raised if level goes below 0."""
        state = TagProcessingState("{% enddiv %}", [])
        state.nested_level = 0 # Already at base level before finding end tag
        match = RE_END_TEST.search(state.current_chunk)
        tag_info = FoundTagInfo(match, False, "div", "{% enddiv %}")
        target_tag = "div"

        with self.assertRaises(NestedTagError):
            handle_nested_end_tag(tag_info, target_tag, state)


class TestProcessNestedContentIntegration(unittest.TestCase):
    """Integration-style tests for the main process_nested_content orchestrator."""

    def setUp(self):
        self.mock_processor = create_mock_processor()

    def test_simple_case_tag_in_first_chunk(self):
        tag = "div"
        first_chunk = " Inner content {% enddiv %} After"
        blocks: List[str] = ["Next block"]

        result = process_nested_content(self.mock_processor, tag, first_chunk, blocks)

        self.assertTrue(result.success)
        self.assertEqual(result.inner_content, "Inner content")
        self.assertEqual(result.remaining_blocks, [" After", "Next block"])

    def test_simple_case_tag_in_next_block(self):
        tag = "div"
        first_chunk = " Inner content line 1"
        blocks = ["Inner content line 2", "{% enddiv %}", "After block"]

        result = process_nested_content(self.mock_processor, tag, first_chunk, blocks)

        self.assertTrue(result.success)
        self.assertEqual(result.inner_content, "Inner content line 1\nInner content line 2")
        self.assertEqual(result.remaining_blocks, ['After block']) # Empty string from after end tag

    def test_basic_nesting(self):
        tag = "outer"
        first_chunk = " Before {% inner %} Inner {% endinner %} After "
        blocks = ["{% endouter %} The very end"]

        result = process_nested_content(self.mock_processor, tag, first_chunk, blocks)

        self.assertTrue(result.success)
        # Inner tags are preserved in the content for recursive parsing later
        self.assertEqual(result.inner_content, "Before {% inner %} Inner {% endinner %} After")
        self.assertEqual(result.remaining_blocks, [" The very end"])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_unclosed_tag(self, mock_stdout):
        tag = "div"
        first_chunk = " Some content "
        blocks = ["More content", "No end tag here"]

        result = process_nested_content(self.mock_processor, tag, first_chunk, blocks)

        self.assertFalse(result.success)
        self.assertEqual(result.inner_content, "Some content \nMore content\nNo end tag here")
        self.assertEqual(result.remaining_blocks, [])
        self.assertIn("Warning: Unclosed custom tag 'div'", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mismatched_tag_at_base_level(self, mock_stdout):
        # Current behavior: Warns about mismatch, continues, finds real end tag
        tag = "div"
        first_chunk = "Content {% endspan %} more {% enddiv %} after"
        blocks: List[str] = []

        with self.assertRaises(NestedTagError):
            process_nested_content(self.mock_processor, tag, first_chunk, blocks)



if __name__ == '__main__':
    unittest.main()