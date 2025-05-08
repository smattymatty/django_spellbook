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
    loop_count = 0

    while True:
        loop_count += 1

        tag_info = find_next_tag_in_chunk(
            processor, state.current_chunk, state.processed_chars
            )

        if tag_info.match:
            content_before_tag = state.current_chunk[state.processed_chars : tag_info.match.start()]
            state.append_content(content_before_tag)

            state.move_past_tag(tag_info.match) # Updates processed_chars

            if tag_info.is_start_tag:
                handle_nested_start_tag(processor, tag_info, state)
            else:
                stop_processing = handle_nested_end_tag(tag_info, tag, state)
                if stop_processing:
                    break
        else:
            # No more tags in this chunk
            remaining_content = state.get_remaining_chunk_content()
            state.append_content(remaining_content)
            state.processed_chars = len(state.current_chunk) # Mark chunk as fully processed

        if state.is_chunk_fully_processed():
            if state.nested_level > 0:
                loaded = state.load_next_block()
                if loaded:
                    pass # No need to print anything here
                else:
                    print(f"Warning: Unclosed custom tag '{tag}'. Reached end of input.")
                    break # Exit loop if no more blocks
            else:
                # Nested level is 0 or less, and chunk is done. We should be finished.
                break # pragma: no cover

    result = state.build_result()
    return result


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


def handle_nested_start_tag(
    processor: 'DjangoLikeTagProcessor', # Pass the processor instance
    tag_info: FoundTagInfo,
    state: TagProcessingState
    ):
    """
    Handles the start of a nested tag.
    Increments nesting level for known Django block tags AND any unrecognized tags
    (assumed to be user-defined blocks like {% div %} or {% mytag %}).
    Does NOT increment level for known Django inline tags (like {% static %}) or
    other built-ins handled differently (like {% else %}).
    """
    tag_name = tag_info.tag_name
    if tag_name is None:
        if tag_info.full_tag_text: state.append_content(tag_info.full_tag_text) # pragma: no cover
        return # pragma: no cover
    # --- Explicitly ignore tags starting with 'end' in the START tag handler ---
    if tag_name.startswith('end'):
        # Do NOT increment level and do NOT append content.
        return # Exit the function early

    # Determine if this tag should increment the nesting level for finding its end tag.
    # We increment for:
    # 1. Known Django block tags ({% if %}, {% for %}, etc.)
    # 2. Any tag NOT recognized as a Django built-in (assumed custom {% tag %}...{% endtag %})
    # We DO NOT increment for:
    # 1. Known Django inline tags ({% static %}, {% url %}, {% load %}, etc.)
    # 2. Other Django built-ins ({% else %}, {% elif %}, {% extends %}, etc.) which don't nest in this way.

    is_block_tag = False # Default assumption
    tag_type = "UNKNOWN" # Default

    
    # Check against known Django tag categories from the processor
    if tag_name in processor.DJANGO_BLOCK_TAGS:
        # Known Django block tag (e.g., if, for) - requires nesting
        is_block_tag = True
        tag_type = "DJANGO_BLOCK"
    elif tag_name in processor.DJANGO_INLINE_TAGS:
        # Known Django inline tag (e.g., static, url) - does not affect nesting here
        is_block_tag = False
        tag_type = "DJANGO_INLINE"
    elif tag_name in processor.DJANGO_BUILT_INS:
        # Another known Django built-in (e.g., else, extends) - does not affect nesting here
        is_block_tag = False
        tag_type = "DJANGO_OTHER_BUILTIN"
    else:
        # Not a known Django built-in - assume it's a user-defined custom block tag
        is_block_tag = True
        tag_type = "CUSTOM_BLOCK"

    # Adjust nesting level based on the determination
    if is_block_tag:
        state.nested_level += 1

    # Always append the original tag text to the inner content for later recursive parsing
    if tag_info.full_tag_text:
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