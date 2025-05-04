from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .django_like import DjangoLikeTagProcessor # pragma: no cover

from django_spellbook.markdown.extensions.tag_stats import (
    FoundTagInfo, NestedContentResult, TagProcessingState
)

import re

class NestedTagError(Exception):
    pass


def process_nested_content(
    processor: 'DjangoLikeTagProcessor',
    tag: str, 
    first_content_chunk: str,
    blocks: List[str]
    ) -> NestedContentResult:
    """ 
    Processes content between custom tags using state machine. 
    
    Args:
        tag: The name of the custom tag (e.g., 'div', 'span').
        first_content_chunk: The content in the initial block after the start tag.
        blocks: The list of subsequent blocks.
        
    Returns:
        NestedContentResult: A tuple containing the inner content, remaining blocks, and a success flag.
    
    """
    state = TagProcessingState(first_content_chunk, blocks)
    while True:
        tag_info = find_next_tag_in_chunk(
            processor, state.current_chunk, state.processed_chars
            )
        if tag_info.match:
            content_before_tag = state.current_chunk[state.processed_chars : tag_info.match.start()]
            state.append_content(content_before_tag)
            state.move_past_tag(tag_info.match)
            if tag_info.is_start_tag:
                handle_nested_start_tag(tag_info, state)
            else:
                stop_processing = handle_nested_end_tag(tag_info, tag, state)
                if stop_processing: break
        else:
            remaining_content = state.get_remaining_chunk_content()
            state.append_content(remaining_content)
            state.processed_chars = len(state.current_chunk)

        if state.is_chunk_fully_processed():
            if state.nested_level > 0:
                if not state.load_next_block():
                    print(f"Warning: Unclosed custom tag '{tag}'. Reached end of input.")
                    break
            else: break # Level 0 or less, chunk done. pragma: no cover

    return state.build_result()


def find_next_tag_in_chunk(
    processor: 'DjangoLikeTagProcessor',
    content_chunk: str, 
    start_pos: int
    ) -> FoundTagInfo:
    """
    Searches for the next tag, starting from the given position.

    Args:
        content_chunk: The content chunk to search in.
        start_pos: The position to start searching from.
        
    Returns:
        FoundTagInfo: A named tuple containing the tag match, start tag flag, tag name, and full tag text.
    """
    start_match = processor.RE_START.search(content_chunk, start_pos)
    end_match = processor.RE_END.search(content_chunk, start_pos)
    next_match: Optional[re.Match] = None
    is_start = False
    if start_match and end_match:
        if start_match.start() < end_match.start(): next_match, is_start = start_match, True
        else: next_match = end_match
    elif start_match: next_match, is_start = start_match, True
    elif end_match: next_match = end_match
    if next_match:
        return FoundTagInfo(next_match, is_start, next_match.group(1), next_match.group(0))
    else:
        return FoundTagInfo(None, False, None, None)


def handle_nested_start_tag(tag_info: FoundTagInfo, state: TagProcessingState):
    """
    Handles the start of a nested tag.

    Args:
        tag_info: The tag info tuple containing the tag match, start tag flag, tag name, and full tag text.
        state: The TagProcessingState object containing the current chunk, processed characters, and nested level.
    """
    if tag_info.tag_name and not tag_info.tag_name.startswith('end'):
        state.nested_level += 1
        state.append_content(tag_info.full_tag_text)


def handle_nested_end_tag(
    tag_info: FoundTagInfo, 
    target_tag: str,
    state: TagProcessingState
    ) -> bool:
    """
    Handles the end of a nested tag.

    Args:
        tag_info: The tag info tuple containing the tag match, start tag flag, tag name, and full tag text.
        target_tag: The name of the tag that is expected to end.
        state: The TagProcessingState object containing the current chunk, processed characters, and nested level.

    Returns:
        True if the end tag was found, False otherwise.
    """
    state.nested_level -= 1
    if state.nested_level == 0:
        if tag_info.tag_name == target_tag:
            state.found_matching_end_tag = True
            remaining_after_end = state.get_remaining_chunk_content()
            if remaining_after_end: state.remaining_blocks.insert(0, remaining_after_end)
            return True # Stop processing
        else:
            print(f"Warning: Found mismatched end tag '{tag_info.full_tag_text}' when expecting '{{% end{target_tag} %}}'. Ignoring.")
            return False # Continue processing
    elif state.nested_level > 0:
        state.append_content(tag_info.full_tag_text)
        return False # Continue processing
    else:
        raise NestedTagError(f"Found end tag '{tag_info.full_tag_text}' processing '{target_tag}'. Balancing issue.")