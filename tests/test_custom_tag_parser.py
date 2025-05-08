import unittest
from unittest.mock import Mock, patch, MagicMock
import io
import re
from typing import List
from django_spellbook.markdown.extensions.django_like import DjangoLikeTagProcessor
from markdown.blockparser import BlockParser
from markdown.core import Markdown

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
    mock_processor = DjangoLikeTagProcessor(BlockParser(Markdown()))
    return mock_processor # Return the processor instance

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
        processor = DjangoLikeTagProcessor(BlockParser(Markdown()))
        state = TagProcessingState("initial", [])
        state.nested_level = 1 # Start at level 1
        # Simulate a FoundTagInfo for a start tag
        match = RE_START_TEST.search("{% div class='foo' %}")
        tag_info = FoundTagInfo(match, True, "div", "{% div class='foo' %}")

        handle_nested_start_tag(processor, tag_info, state)

        self.assertEqual(state.nested_level, 2) # Level incremented
        self.assertEqual(state.collected_parts, ["{% div class='foo' %}"]) # Tag added

    def test_ignores_start_tag_named_end(self):
        """Should ignore tags like {% endcustom %} if accidentally matched by RE_START."""
        processor = DjangoLikeTagProcessor(BlockParser(Markdown()))
        state = TagProcessingState("initial", [])
        state.nested_level = 1
        match = RE_START_TEST.search("{% enddiv %}") # RE_START *can* match this
        tag_info = FoundTagInfo(match, True, "enddiv", "{% enddiv %}") # is_start=True, name starts with 'end'

        handle_nested_start_tag(processor, tag_info, state)

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




# --- Test Class ---

class TestHandleNestedStartTagTagTypes(unittest.TestCase):
    """
    Tests focusing on tag type determination within handle_nested_start_tag.
    """

    def setUp(self):
        """Set up a processor instance and initial state for each test."""
        # Use the real processor to get access to its class-level tag sets
        self.processor = DjangoLikeTagProcessor(BlockParser(Markdown()))
        self.initial_level = 1
        self.state = TagProcessingState("dummy content", [])
        self.state.nested_level = self.initial_level

    def test_handles_django_block_tag_correctly(self):
        """
        Verify DJANGO_BLOCK type: 'if' tag should increment level and append text.
        """
        tag_name = 'if' # Example from DJANGO_BLOCK_TAGS
        self.assertIn(tag_name, self.processor.DJANGO_BLOCK_TAGS) # Sanity check test setup
        full_tag_text = '{% if user.is_authenticated %}'
        # Simulate FoundTagInfo as it would come from find_next_tag_in_chunk
        tag_info = FoundTagInfo(MagicMock(), True, tag_name, full_tag_text) # is_start=True

        handle_nested_start_tag(self.processor, tag_info, self.state)

        # Check expectations for DJANGO_BLOCK type
        self.assertEqual(self.state.nested_level, self.initial_level + 1,
                         f"'{tag_name}' (DJANGO_BLOCK) should increment nesting level.")
        self.assertEqual(self.state.collected_parts, [full_tag_text],
                         "Tag text should be appended.")

    def test_handles_django_other_builtin_tag_correctly(self):
        """
        Verify DJANGO_OTHER_BUILTIN type: 'else' tag should NOT increment level but append text.
        """
        tag_name = 'else' # Example built-in not in BLOCK_TAGS or INLINE_TAGS
        self.assertNotIn(tag_name, self.processor.DJANGO_BLOCK_TAGS)
        self.assertNotIn(tag_name, self.processor.DJANGO_INLINE_TAGS)
        self.assertIn(tag_name, self.processor.DJANGO_BUILT_INS) # Sanity checks
        full_tag_text = '{% else %}'
        tag_info = FoundTagInfo(MagicMock(), True, tag_name, full_tag_text) # is_start=True

        handle_nested_start_tag(self.processor, tag_info, self.state)

        # Check expectations for DJANGO_OTHER_BUILTIN type
        self.assertEqual(self.state.nested_level, self.initial_level,
                         f"'{tag_name}' (DJANGO_OTHER_BUILTIN) should NOT increment nesting level.")
        self.assertEqual(self.state.collected_parts, [full_tag_text],
                         "Tag text should still be appended.")

    def test_handles_django_inline_tag_correctly(self):
        """
        Verify DJANGO_INLINE type: 'static' tag should NOT increment level but append text.
        (Added for completeness)
        """
        tag_name = 'static' # Example from DJANGO_INLINE_TAGS
        self.assertIn(tag_name, self.processor.DJANGO_INLINE_TAGS) # Sanity check
        full_tag_text = '{% static "style.css" %}'
        tag_info = FoundTagInfo(MagicMock(), True, tag_name, full_tag_text) # is_start=True

        handle_nested_start_tag(self.processor, tag_info, self.state)

        # Check expectations for DJANGO_INLINE type
        self.assertEqual(self.state.nested_level, self.initial_level,
                         f"'{tag_name}' (DJANGO_INLINE) should NOT increment nesting level.")
        self.assertEqual(self.state.collected_parts, [full_tag_text],
                         "Tag text should be appended.")

    def test_handles_custom_block_tag_correctly(self):
        """
        Verify CUSTOM_BLOCK type: 'div' tag should increment level and append text.
        (Added for completeness)
        """
        tag_name = 'div' # Example custom tag (not in any DJANGO_* sets)
        self.assertNotIn(tag_name, self.processor.DJANGO_BUILT_INS) # Sanity check
        full_tag_text = '{% div class="foo" %}'
        tag_info = FoundTagInfo(MagicMock(), True, tag_name, full_tag_text) # is_start=True

        handle_nested_start_tag(self.processor, tag_info, self.state)

        # Check expectations for CUSTOM_BLOCK type
        self.assertEqual(self.state.nested_level, self.initial_level + 1,
                         f"'{tag_name}' (CUSTOM_BLOCK) should increment nesting level.")
        self.assertEqual(self.state.collected_parts, [full_tag_text],
                         "Tag text should be appended.")

    def test_ignores_tag_starting_with_end(self):
        """
        Verify explicit check: '{% enddiv %}' should NOT increment level and NOT append text.
        (Verifies the fix for the previous test failure)
        """
        tag_name = 'enddiv' # Starts with 'end'
        full_tag_text = '{% enddiv %}'
        tag_info = FoundTagInfo(MagicMock(), True, tag_name, full_tag_text) # is_start=True

        handle_nested_start_tag(self.processor, tag_info, self.state)

        # Check expectations for tags starting with 'end'
        self.assertEqual(self.state.nested_level, self.initial_level,
                         f"'{tag_name}' (starts with 'end') should NOT increment nesting level.")
        self.assertEqual(self.state.collected_parts, [], # Should be empty now
                         "Tag text should NOT be appended.")
        
        

if __name__ == '__main__':
    unittest.main()
    