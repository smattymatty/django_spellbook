import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree
from typing import List, Optional, Dict, Any, Tuple

# Assuming attribute_parser.py is in the same directory or install path
from django_spellbook.markdown.attribute_parser import parse_attributes # Needed for mocking if _parse_attributes is tested directly

# Note: These imports might be used elsewhere in the actual file.
from django.template import Template, Context
from django.template.loader import render_to_string

class NestedTagError(Exception):
    pass


class DjangoLikeTagProcessor(BlockProcessor):
    """
    A Markdown block processor that handles Django-like template tags.

    This processor allows using Django-style template tags within markdown content,
    supporting both custom HTML elements with attributes and built-in Django template tags.
    It uses an external parser to handle attribute string parsing, including shortcuts.

    Supported syntax:
    - Custom elements: {% tag class="value" id="myid" %}content{% endtag %}
    - Class shortcuts: {% tag .classname %}content{% endtag %}
    - ID shortcuts: {% tag #myid %}content{% endtag %}
    - Built-in Django tags: {% url 'name' %}, {% static 'path' %}, {% include 'template' %}

    Attributes:
        DJANGO_BUILT_INS (set): Set of built-in Django template tags to preserve.
        DJANGO_BLOCK_TAGS (dict): Mapping of Django block tags to their closing tags.
        RE_START (Pattern): Regex for matching opening tags {% tag ... %}.
        RE_END (Pattern): Regex for matching closing tags {% endtag %}.
    """

    DJANGO_BUILT_INS = {
        'static', 'url', 'include', 'if', 'for', 'block',
        'extends', 'load', 'with', 'csrf_token'
    }

    DJANGO_BLOCK_TAGS = {
        'if': 'endif',
        'for': 'endfor',
        'block': 'endblock',
        'with': 'endwith',
    }

    # Regex for start and end tags remain
    RE_START = re.compile(r'{%\s*(\w+)([\s\S]*?)%}') # Capture tag name and everything else
    RE_END = re.compile(r'{%\s*end(\w+)\s*%}') # Capture closing tag name

    def test(self, parent: ElementTree.Element, block: str) -> bool:
        """
        Test if the block contains a valid opening Django-like tag.

        Args:
            parent: Parent XML element.
            block: Text block to test.

        Returns:
            True if block contains a potential Django-like opening tag
            that doesn't start with 'end'.
        """
        match = self.RE_START.search(block)
        # Ensure a match exists AND the tag name doesn't start with 'end'
        return bool(match and not match.group(1).startswith('end'))


    def run(self, parent: ElementTree.Element, blocks: List[str]) -> bool:
        """
        Process the block and handle Django-like tags.

        Args:
            parent: Parent XML element.
            blocks: List of text blocks to process.

        Returns:
            True if processing was successful, False otherwise.
        """
        original_block = blocks.pop(0)
        match = self.RE_START.search(original_block)

        # Ensure it's a valid starting tag before proceeding
        if not match or match.group(1).startswith('end'):
            blocks.insert(0, original_block) # Put the block back
            return False

        tag = match.group(1)
        attrs_string = match.group(2).strip() # Raw string after tag name

        # Process content before the matched tag
        before = original_block[:match.start()]
        if before:
            # Use parseBlocks for potentially multi-line 'before' content
            self.parser.parseBlocks(parent, [before])

        # Content in the original block *after* the opening tag's end
        remaining_content_in_block = original_block[match.end():]

        # --- Dispatch based on tag type ---
        if tag in self.DJANGO_BUILT_INS:
            # Pass the original blocks list (now without original_block)
            return self._handle_django_tag(parent, blocks, remaining_content_in_block, match)
        else:
            # Pass the original blocks list (now without original_block)
            return self._handle_custom_element(parent, blocks, remaining_content_in_block, tag, attrs_string)


    def _handle_django_tag(self, parent: ElementTree.Element,
                           blocks: List[str], first_content_chunk: str,
                           match: re.Match) -> bool:
        """
        Handle built-in Django template tags (single or block).

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: The portion of the original block after the opening tag.
            match: Regex match object for the opening tag.

        Returns:
            True if processing was successful.
        """
        tag = match.group(1)
        full_opening_tag = match.group(0) # The complete {% ... %} tag text

        # Handle block-level Django tags ({% if %}, {% for %}, etc.)
        if tag in self.DJANGO_BLOCK_TAGS:
            # Pass the blocks list as received
            return self._handle_django_block_tag(parent, blocks, first_content_chunk, tag, full_opening_tag)

        # Handle single Django tags ({% url %}, {% static %}, etc.)
        tag_element = ElementTree.SubElement(parent, 'django-tag')
        tag_element.text = full_opening_tag

        # Put the remaining content from the original block back at the
        # beginning of the blocks list for standard parsing.
        if first_content_chunk:
            blocks.insert(0, first_content_chunk)

        return True

    def _handle_django_block_tag(self, parent: ElementTree.Element,
                                 blocks: List[str], first_content_chunk: str,
                                 tag: str, full_opening_tag: str) -> bool:
        """
        Handle Django block-level tags like if, for, block, with.

        Finds the matching end tag and processes content in between.
        Preserves the start and end tags using generic <django-tag> elements.

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: The portion of the original block after the opening tag.
            tag: The name of the Django block tag (e.g., 'if', 'for').
            full_opening_tag: The complete text of the opening tag ({% if condition %}).

        Returns:
            True if processing was successful.
        """
        end_tag_name = self.DJANGO_BLOCK_TAGS.get(tag)

        # Add the opening tag element
        opening_tag_element = ElementTree.SubElement(parent, 'django-tag')
        opening_tag_element.text = full_opening_tag

        # --- Extract content between tags ---
        end_tag_pattern = f'{{% {end_tag_name} %}}'
        content_parts = [] # Initialize empty
        end_tag_found = False
        after_content = '' # Content after the end tag in its block
        temp_blocks = blocks.copy() # Work with a copy

        current_chunk = first_content_chunk # Start searching in the first chunk

        while True: # Loop through current_chunk and then subsequent blocks
            partition_index = current_chunk.find(end_tag_pattern)

            if partition_index != -1:
                # Found the end tag in this chunk
                content_before_end = current_chunk[:partition_index]
                after_content = current_chunk[partition_index + len(end_tag_pattern):]
                # Add only the content *before* the end tag from this chunk
                content_parts.append(content_before_end)
                end_tag_found = True
                break # Stop consuming blocks/chunks
            else:
                # End tag not found in this chunk, add the whole chunk to content
                content_parts.append(current_chunk)
                # Try getting the next block
                if temp_blocks:
                    current_chunk = temp_blocks.pop(0) # Get next block
                else:
                    # No more blocks and end tag not found
                    end_tag_found = False
                    break

        # Join collected parts. This now correctly excludes the opening tag's parameters.
        inner_content = '\n'.join(content_parts).strip()

        # Process inner content recursively *only if* there is content
        if inner_content:
             # parseBlocks expects a list of blocks. Split the processed content.
             self.parser.parseBlocks(parent, inner_content.split('\n\n'))

        # Add the closing tag element *only if the end tag was found*
        if end_tag_found:
            closing_tag_element = ElementTree.SubElement(parent, 'django-tag')
            closing_tag_element.text = end_tag_pattern
        else:
             # Warn if end tag wasn't found
            print(f"Warning: Unclosed Django block tag '{tag}' looking for '{end_tag_pattern}'.")

        # Update the original blocks list with remaining blocks and any content after the end tag
        blocks[:] = temp_blocks # Assign remaining blocks from the copy
        if after_content:
            blocks.insert(0, after_content) # Add content after end tag back

        return True # Return true even if unclosed, as we processed up to that point

    def _process_nested_content(self, tag: str, first_content_chunk: str, blocks: List[str]) -> Tuple[str, List[str]]:
        """
        Process content between a custom start tag and its matching end tag.

        Handles nested tags and consumes blocks as needed. Returns the inner
        content (including any nested tags for recursive parsing) and the
        list of remaining blocks after the matching end tag. This method ensures
        the matching end tag itself is *not* included in the returned content.

        Args:
            tag: The name of the custom tag (e.g., 'div', 'span').
            first_content_chunk: The content in the initial block after the start tag.
            blocks: The list of subsequent blocks.

        Returns:
            A tuple containing:
            - The collected content string *between* the start and matching end tags.
            - The updated list of remaining blocks after the end tag.
        """
        nested_level = 1
        collected_content_parts = []
        current_content = first_content_chunk
        # Make a copy to safely pop from or modify
        remaining_blocks = blocks.copy()

        processed_chars_in_current = 0 # Track position within current_content

        while True: # Loop through content chunks/blocks
            # Find the *next* relevant tag (start or end) from the current position
            # Ensure RE_START doesn't accidentally match {% end... %} tags if possible,
            # though RE_END is more specific.
            # A simple negative lookahead could help RE_START if needed: r'{%\s*(?!end)(\w+)([\s\S]*?)%}'
            # But let's rely on processing order for now.
            start_match = self.RE_START.search(current_content, processed_chars_in_current)
            end_match = self.RE_END.search(current_content, processed_chars_in_current)

            # Determine which tag comes first, if any
            next_match = None
            is_start = False
            if start_match and end_match:
                if start_match.start() < end_match.start():
                    next_match = start_match
                    is_start = True
                else:
                    next_match = end_match
            elif start_match:
                next_match = start_match
                is_start = True
            elif end_match: # pragma: no cover
                next_match = end_match # pragma: no cover
            # else: no more tags in this chunk

            if next_match:
                # --- Process content BEFORE the tag ---
                content_before = current_content[processed_chars_in_current : next_match.start()]
                if content_before: # Avoid adding empty strings
                    collected_content_parts.append(content_before)
                # Move position *past* the tag for the next search iteration
                processed_chars_in_current = next_match.end()

                # --- Process the tag itself ---
                tag_text = next_match.group(0)
                tag_name = next_match.group(1)

                if is_start:
                    # It's a start tag {% tag ... %}
                    # Increment level *only* if it's not an end tag misidentified by RE_START
                    if not tag_name.startswith('end'):
                        nested_level += 1
                        # Include the start tag's text for potential recursive processing
                        collected_content_parts.append(tag_text)
                    # else: Silently ignore {% end... %} possibly caught by RE_START

                else: # It's an end tag {% endtag %} matched by RE_END
                    # Decrement level *before* checking match
                    current_level_before_decrement = nested_level
                    nested_level -= 1

                    if nested_level == 0:
                        # Reached base level. Does this end tag match our starting tag?
                        if tag_name == tag:
                            # Success! Found the correct closing tag.
                            # Preserve content *after* this closing tag in its block.
                            remaining_after_end = current_content[processed_chars_in_current:]
                            if remaining_after_end:
                                remaining_blocks.insert(0, remaining_after_end)
                            # Return collected content (WITHOUT this end tag) and remaining blocks
                            # Use rstrip to remove potential trailing whitespace before the end tag
                            return ''.join(collected_content_parts).rstrip(), remaining_blocks
                        else:
                            # Mismatched end tag at the base level!
                            # e.g., started with {% div %}, found {% endspan %} when level was 1.
                            print(f"Warning: Found mismatched end tag '{tag_text}' when expecting '{{% end{tag} %}}'. Ignoring it and continuing search.")
                            # We consumed the tag, level is now 0, but we didn't find the right one.
                            # Continue the loop to search for the correct tag from the current position.
                            pass

                    elif nested_level > 0:
                        # This end tag closes a nested block correctly.
                        # Include its text for recursive parsing.
                        collected_content_parts.append(tag_text)
                        # Continue the loop

                    else: # nested_level < 0
                        # More end tags than start tags encountered *before* finding the correct one.

                        # We consumed the tag, continue searching in the current chunk.
                        raise NestedTagError(
                            f"Found end tag '{tag_text}' while processing outer tag '{tag}'. Check tag balancing.\n"\
                            f"Nesting Django-like tags is not supported. Instead, nest Spellblocks!\n\n"\
                            f"https://django-spellbook.org/docs/Spellblocks/introduction/\n\n"\
                            f"Django-Like tags should be used minimally and only one at a time. Spellblocks allow for more complex nesting."
                                             )

            else:
                # No more tags found in the *rest* of the current chunk.
                content_after_last_tag = current_content[processed_chars_in_current:]
                if content_after_last_tag:
                    collected_content_parts.append(content_after_last_tag)
                processed_chars_in_current = len(current_content) # Mark chunk as done

            # --- Check if we need the next block ---
            # Use '>=' comparison for processed_chars_in_current
            if processed_chars_in_current >= len(current_content) and nested_level > 0:
                if remaining_blocks:
                    # Get the next block
                    current_content = remaining_blocks.pop(0)
                     # Add newline separator only if there was previous content from *this* scope
                    if collected_content_parts and not ''.join(collected_content_parts).endswith('\n'):
                         collected_content_parts.append('\n')
                    processed_chars_in_current = 0 # Reset position for new block
                else:
                    # No more blocks, but nesting level > 0 means unclosed tag
                    print(f"Warning: Unclosed custom tag '{tag}' found. Reached end of input.")
                    break # Exit loop, return collected content so far

        # If loop finishes (found tag and returned, or ran out of blocks)
        # Return whatever content we collected and the blocks remaining *after* processing
        # Use strip() on the final result to clean whitespace at ends.
        return ''.join(collected_content_parts).strip(), remaining_blocks


    def _handle_custom_element(self, parent: ElementTree.Element,
                               blocks: List[str], first_content_chunk: str,
                               tag: str, attrs_string: str) -> bool:
        """
        Handle custom HTML-like elements {% tag ... %}content{% endtag %}.

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: The portion of the original block after the opening tag.
            tag: The tag name (e.g., 'div').
            attrs_string: The raw attribute string from the opening tag.

        Returns:
            True if processing was successful.
        """
        element = ElementTree.SubElement(parent, tag)
        self._parse_attributes(element, attrs_string)

        # Process content between tags using the refactored method
        # Pass the blocks list received from run
        content, remaining_blocks_after = self._process_nested_content(tag, first_content_chunk, blocks)

        # Parse the extracted content recursively using parseBlocks.
        if content: # Check if content is not empty after potential strip() in _process_nested_content
            # Split content into blocks based on blank lines for proper Markdown processing
            self.parser.parseBlocks(element, content.split('\n\n'))

        # Update the original blocks list with what's left after the closing tag
        blocks[:] = remaining_blocks_after # Update the list in place
        return True

    def _parse_attributes(self, element: ElementTree.Element, attrs_string: str) -> None:
        """
        Parse the attribute string and set attributes on the element.

        Delegates parsing to the external `parse_attributes` function.

        Args:
            element: The ElementTree element to set attributes on.
            attrs_string: The raw attribute string.
        """
        attributes = parse_attributes(attrs_string)
        for key, value in attributes.items():
            element.set(key, value)


class DjangoLikeTagExtension(Extension):
    """
    Markdown extension for handling Django-like template tags.

    Registers the DjangoLikeTagProcessor.
    """
    def extendMarkdown(self, md) -> None:
        """Register the processor."""
        md.parser.blockprocessors.register(
            DjangoLikeTagProcessor(md.parser), 'django_like_tag', 175)


def makeExtension(**kwargs) -> DjangoLikeTagExtension:
    """Factory function."""
    return DjangoLikeTagExtension(**kwargs)
