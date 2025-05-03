import unittest
from xml.etree import ElementTree
from typing import List

# Import the functions and the NamedTuple to be tested
from django_spellbook.markdown.extensions.django_builtin_tag_helpers import (
    find_django_end_tag_and_extract_content,
    parse_inner_content, # We'll need mocking for this later
    add_django_tag_element,
    handle_unclosed_django_tag, # We'll need stdout capture for this later
    update_blocks_after_processing,
    handle_django_block_tag,
    DjangoBlockContentResult # Import the NamedTuple
)

# We might need mock objects later for testing functions that depend on the processor
from unittest.mock import Mock, patch
import io # To capture print output


class TestFindDjangoEndTag(unittest.TestCase):
    """Tests for the find_django_end_tag_and_extract_content function."""

    def test_tag_found_in_first_chunk(self):
        """End tag found within the first content chunk."""
        first_chunk = "Some content {% endif %} more content"
        input_blocks: List[str] = ["block2", "block3"]
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="Some content",
            end_tag_found=True,
            remaining_blocks=["block2", "block3"], # Input blocks untouched
            after_end_tag_content=" more content"
        )
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

    def test_tag_found_in_subsequent_block(self):
        """End tag found in a block from the input_blocks list."""
        first_chunk = "Some content"
        input_blocks = ["block2 line1\nblock2 line2", "block3 {% endif %} after tag", "block4"]
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="Some content\nblock2 line1\nblock2 line2\nblock3",
            end_tag_found=True,
            remaining_blocks=["block4"], # block4 remains after consuming block3
            after_end_tag_content=" after tag"
        )
        # input_blocks.copy() is used inside the function, so original list isn't needed here
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

    def test_tag_not_found(self):
        """End tag is not found anywhere."""
        first_chunk = "Some content"
        input_blocks = ["block2", "block3"]
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="Some content\nblock2\nblock3", # All content collected
            end_tag_found=False,
            remaining_blocks=[], # All blocks consumed
            after_end_tag_content=""
        )
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

    def test_tag_at_start_of_first_chunk(self):
        """End tag is at the very beginning of the first chunk."""
        first_chunk = "{% endif %} after tag"
        input_blocks: List[str] = ["block2"]
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="", # No content before tag
            end_tag_found=True,
            remaining_blocks=["block2"],
            after_end_tag_content=" after tag"
        )
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

    def test_tag_at_end_of_block(self):
        """End tag is at the very end of a block."""
        first_chunk = "Some content"
        input_blocks = ["block2 part1 {% endif %}"] # Tag at end of block
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="Some content\nblock2 part1", # Trailing space
            end_tag_found=True,
            remaining_blocks=[], # Block containing tag was consumed
            after_end_tag_content="" # Nothing after tag
        )
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

    def test_empty_inputs(self):
        """Test with empty first chunk and blocks."""
        first_chunk = ""
        input_blocks: List[str] = []
        end_tag_pattern = "{% endif %}"

        expected_result = DjangoBlockContentResult(
            inner_content="",
            end_tag_found=False,
            remaining_blocks=[],
            after_end_tag_content=""
        )
        result = find_django_end_tag_and_extract_content(first_chunk, input_blocks, end_tag_pattern)
        self.assertEqual(result, expected_result)

# --- Test class for update_blocks_after_processing ---
class TestUpdateBlocks(unittest.TestCase):

    def test_update_with_remaining_blocks_and_after_content(self):
        original_blocks = ["old1", "old2"] # This will be modified in place
        remaining_after = ["new1", "new2"]
        after_content = "after tag content"

        # Expected state of original_blocks after call
        expected_blocks = ["after tag content", "new1", "new2"]

        update_blocks_after_processing(original_blocks, remaining_after, after_content)
        self.assertEqual(original_blocks, expected_blocks)

    def test_update_with_no_remaining_blocks(self):
        original_blocks = ["old1", "old2"]
        remaining_after: List[str] = []
        after_content = "after tag content"
        expected_blocks = ["after tag content"]
        update_blocks_after_processing(original_blocks, remaining_after, after_content)
        self.assertEqual(original_blocks, expected_blocks)

    def test_update_with_no_after_content(self):
        original_blocks = ["old1", "old2"]
        remaining_after = ["new1", "new2"]
        after_content = ""
        expected_blocks = ["new1", "new2"]
        update_blocks_after_processing(original_blocks, remaining_after, after_content)
        self.assertEqual(original_blocks, expected_blocks)

    def test_update_with_no_remaining_blocks_or_after_content(self):
        original_blocks = ["old1", "old2"]
        remaining_after: List[str] = []
        after_content = ""
        expected_blocks: List[str] = []
        update_blocks_after_processing(original_blocks, remaining_after, after_content)
        self.assertEqual(original_blocks, expected_blocks)


# --- Test class for add_django_tag_element ---
class TestAddDjangoTagElement(unittest.TestCase):

    def test_adds_correct_element_and_text(self):
        parent = ElementTree.Element("div")
        tag_text = "{% if condition %}"
        add_django_tag_element(parent, tag_text)

        # Check if one child was added
        self.assertEqual(len(list(parent)), 1)
        # Find the added element
        added_element = parent.find("django-tag")
        self.assertIsNotNone(added_element)
        # Check its tag name and text content
        self.assertEqual(added_element.tag, "django-tag")
        self.assertEqual(added_element.text, tag_text)


# --- Test class for handle_unclosed_django_tag ---
class TestHandleUnclosedTag(unittest.TestCase):

    # Use unittest.mock.patch to capture stdout
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_prints_correct_warning(self, mock_stdout):
        tag_name = "if"
        end_tag_pattern = "{% endif %}"
        expected_warning = f"Warning: Unclosed Django block tag '{tag_name}' looking for '{end_tag_pattern}'.\n"

        handle_unclosed_django_tag(tag_name, end_tag_pattern)

        # Check if the captured output matches the expected warning
        self.assertEqual(mock_stdout.getvalue(), expected_warning)


# --- Test class for parse_inner_content (Requires Mocking) ---
class TestParseInnerContent(unittest.TestCase):

    def test_calls_parser_with_split_blocks(self):
        # Create a mock processor object
        mock_processor = Mock()
        # Mock the parser and its parseBlocks method within the processor
        mock_processor.parser = Mock()
        mock_processor.parser.parseBlocks = Mock()

        parent = ElementTree.Element("div")
        inner_content = "Paragraph 1.\n\nParagraph 2.\nMore P2."
        # Expected list of blocks after splitting
        expected_blocks_arg = ["Paragraph 1.", "Paragraph 2.\nMore P2."]

        parse_inner_content(mock_processor, parent, inner_content)

        # Assert that parseBlocks was called once with the correct arguments
        mock_processor.parser.parseBlocks.assert_called_once_with(parent, expected_blocks_arg)

    def test_does_not_call_parser_with_empty_content(self):
        # Create mocks
        mock_processor = Mock()
        mock_processor.parser = Mock()
        mock_processor.parser.parseBlocks = Mock()

        parent = ElementTree.Element("div")
        inner_content = "" # Empty or whitespace only

        parse_inner_content(mock_processor, parent, inner_content)

        # Assert that parseBlocks was *not* called
        mock_processor.parser.parseBlocks.assert_not_called()

# --- Test class for handle_django_block_tag (Integration - More Mocking) ---
# Testing this orchestrator function requires mocking the helpers it calls
# This can become complex, but ensures the orchestration logic is correct.
# Example sketch:
class TestHandleDjangoBlockTagOrchestration(unittest.TestCase):

    @patch('django_spellbook.markdown.extensions.django_builtin_tag_helpers.find_django_end_tag_and_extract_content')
    @patch('django_spellbook.markdown.extensions.django_builtin_tag_helpers.add_django_tag_element')
    @patch('django_spellbook.markdown.extensions.django_builtin_tag_helpers.parse_inner_content')
    @patch('django_spellbook.markdown.extensions.django_builtin_tag_helpers.handle_unclosed_django_tag')
    @patch('django_spellbook.markdown.extensions.django_builtin_tag_helpers.update_blocks_after_processing')
    def test_orchestration_when_tag_found(self, mock_update, mock_handle_unclosed, mock_parse, mock_add, mock_find):

        # 1. Setup Mocks
        mock_processor = Mock()
        mock_processor.DJANGO_BLOCK_TAGS = {'if': 'endif'}
        parent = ElementTree.Element("div")
        blocks = ["original_block2"]
        first_chunk = " content {% if condition %}" # Content doesn't matter much here
        tag = "if"
        full_opening_tag = "{% if condition %}"

        # Configure the mock return value for the find function
        find_result = DjangoBlockContentResult(
            inner_content="Found inner content",
            end_tag_found=True,
            remaining_blocks=["block_after_end"],
            after_end_tag_content="content_after_end"
        )
        mock_find.return_value = find_result

        # 2. Call the orchestrator function
        result = handle_django_block_tag(mock_processor, parent, blocks, first_chunk, tag, full_opening_tag)

        # 3. Assertions
        self.assertTrue(result) # Should return True

        # Check that find was called correctly
        mock_find.assert_called_once() # Add more specific args check if needed

        # Check that add_django_tag_element was called twice (open and close)
        self.assertEqual(mock_add.call_count, 2)
        mock_add.assert_any_call(parent, full_opening_tag)
        mock_add.assert_any_call(parent, "{% endif %}") # The expected end tag pattern

        # Check parse_inner_content call
        mock_parse.assert_called_once_with(mock_processor, parent, find_result.inner_content)

        # Check that handle_unclosed was *not* called
        mock_handle_unclosed.assert_not_called()

        # Check update_blocks_after_processing call
        mock_update.assert_called_once_with(blocks, find_result.remaining_blocks, find_result.after_end_tag_content)

    # Add another test case for when end_tag_found is False,
    # asserting that handle_unclosed_django_tag *is* called,
    # and add_django_tag_element is only called once (for opening tag).


if __name__ == '__main__':
    unittest.main()