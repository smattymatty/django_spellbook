# django_spellbook/markdown/extensions/tag_stats.py

from typing import Tuple, List, Optional, NamedTuple
import re
# Define a simple structure to hold tag finding results for clarity
class FoundTagInfo(NamedTuple):
    match: Optional[re.Match]
    is_start_tag: bool
    tag_name: Optional[str]
    full_tag_text: Optional[str]

class NestedContentResult(NamedTuple):
    """Result structure for nested content processing."""
    inner_content: str
    remaining_blocks: List[str]
    success: bool # Indicates if the matching end tag was found

class TagProcessingState:
    """
    Manages the state variables during the parsing of nested custom tags.

    Attributes:
        nested_level: Current depth of tag nesting (starts at 1).
        collected_parts: List of strings building the inner content.
        current_chunk: The current string block being processed.
        remaining_blocks: List of subsequent blocks yet to be processed.
        processed_chars: Index indicating the position processed so far within current_chunk.
        found_matching_end_tag: Flag indicating if the correct closing tag was found.
    """
    def __init__(self, initial_chunk: str, initial_blocks: List[str]):
        self.nested_level: int = 1
        self.collected_parts: List[str] = []
        self.current_chunk: str = initial_chunk
        self.remaining_blocks: List[str] = initial_blocks.copy()
        self.processed_chars: int = 0
        self.found_matching_end_tag: bool = False # Track success explicitly

    def append_content(self, text: str):
        """Appends non-empty text to the collected parts."""
        if text:
            self.collected_parts.append(text)

    def get_remaining_chunk_content(self) -> str:
        """Returns the unprocessed part of the current chunk."""
        return self.current_chunk[self.processed_chars:]

    def move_past_tag(self, match: re.Match):
        """Moves the processed character index past the given match."""
        self.processed_chars = match.end()

    def is_chunk_fully_processed(self) -> bool:
        """Checks if the current chunk has been fully processed."""
        return self.processed_chars >= len(self.current_chunk)

    def load_next_block(self) -> bool:
        """Loads the next block if available. Returns True if successful, False otherwise."""
        if self.remaining_blocks:
            # Add newline separator if adding a new block after some content
            # But only if the collected parts don't already end with substantial whitespace
            last_part = ''.join(self.collected_parts).rstrip()
            if last_part and not last_part.endswith('\n'):
                 self.collected_parts.append('\n')

            self.current_chunk = self.remaining_blocks.pop(0)
            self.processed_chars = 0
            return True
        else:
            return False # No more blocks available

    def build_result(self) -> NestedContentResult:
         """Builds the final result tuple."""
         # Use strip() on the final result to clean whitespace at ends.
         final_content = ''.join(self.collected_parts).strip()
         return NestedContentResult(final_content, self.remaining_blocks, self.found_matching_end_tag)