# django_spellbook/markdown/extensions/django_builtin_tag_helpers.py
from typing import List, NamedTuple
from xml.etree import ElementTree

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .django_like import DjangoLikeTagProcessor # pragma: no cover

class DjangoBlockContentResult(NamedTuple):
    """Holds the result of finding content between Django block tags."""
    inner_content: str
    end_tag_found: bool
    remaining_blocks: List[str]
    after_end_tag_content: str

def handle_django_block_tag(
        processor: 'DjangoLikeTagProcessor', # Pass the processor instance
        parent: ElementTree.Element,
        blocks: List[str], first_content_chunk: str,
        tag: str, full_opening_tag: str
        ) -> bool:
        """
        Handles Django block-level tags (e.g., {% if %}, {% for %}).
        
        Orchestrates finding the end tag, preserving tags, parsing inner content,
        and updating the block list. Refactored for clarity.

        Args:
            parent: Parent XML element.
            blocks: List of subsequent text blocks (passed from run).
            first_content_chunk: Portion of the original block after the opening tag.
            tag: Name of the Django block tag (e.g., 'if').
            full_opening_tag: Complete text of the opening tag ({% if condition %}).

        Returns:
            True, indicating processing was attempted (even if tag was unclosed).
        """
        end_tag_name = processor.DJANGO_BLOCK_TAGS.get(tag)
        if not end_tag_name:
            print(f"Error: Unknown Django block tag '{tag}' encountered.") # pragma: no cover
            return False # pragma: no cover

        end_tag_pattern = f'{{% {end_tag_name} %}}'

        add_django_tag_element(parent, full_opening_tag)

        # --- Use the NamedTuple for the return value ---
        result: DjangoBlockContentResult = find_django_end_tag_and_extract_content(
            first_content_chunk, blocks.copy(), end_tag_pattern
        )
        # --- Access results using named attributes ---

        # Parse the content found between the tags
        parse_inner_content(
            processor, parent, result.inner_content
            )

        # Preserve the closing tag (or warn if not found)
        if result.end_tag_found: # Use result.end_tag_found
            add_django_tag_element(parent, end_tag_pattern)
        else:
            handle_unclosed_django_tag(tag, end_tag_pattern)

        # Update the main 'blocks' list for subsequent Markdown processing
        update_blocks_after_processing(
            blocks, result.remaining_blocks, result.after_end_tag_content
            )

        # TODO: Handle when unclosed tag is found
        
        return True # Assume processed

def find_django_end_tag_and_extract_content(
        first_chunk: str,
        input_blocks: List[str],
        end_tag_pattern: str
    ) -> DjangoBlockContentResult: # <-- Update return type hint
        """
        Searches for the end tag, collecting content blocks until found.
        (Other parts of docstring remain the same)

        Returns:
            DjangoBlockContentResult: An object containing the results.
        """
        content_parts = []
        end_tag_found = False
        after_end_tag_content = ''
        remaining_blocks = input_blocks.copy()
        current_chunk = first_chunk

        while True:
            partition_index = current_chunk.find(end_tag_pattern)
            if partition_index != -1:
                content_before_end = current_chunk[:partition_index]
                after_end_tag_content = current_chunk[partition_index + len(end_tag_pattern):]
                content_parts.append(content_before_end)
                end_tag_found = True
                break
            else:
                content_parts.append(current_chunk)
                if remaining_blocks:
                    current_chunk = remaining_blocks.pop(0)
                else:
                    end_tag_found = False
                    break

        inner_content = '\n'.join(content_parts).strip()
        # --- Return an instance of the NamedTuple ---
        return DjangoBlockContentResult(
            inner_content=inner_content,
            end_tag_found=end_tag_found,
            remaining_blocks=remaining_blocks,
            after_end_tag_content=after_end_tag_content
        )


def parse_inner_content(
    processor: 'DjangoLikeTagProcessor',
    parent: ElementTree.Element,
    inner_content: str
    ) -> None:
        """Parses the extracted inner content using the Markdown parser."""
        if inner_content:
            processor.parser.parseBlocks(parent, inner_content.split('\n\n'))


def add_django_tag_element(parent: ElementTree.Element, tag_text: str) -> None:
        """Adds a <django-tag> element preserving the given tag text."""
        tag_element = ElementTree.SubElement(parent, 'django-tag')
        tag_element.text = tag_text


def handle_unclosed_django_tag(tag_name: str, end_tag_pattern: str) -> None:
        """Handles the case where a closing Django tag was not found."""
        print(f"Warning: Unclosed Django block tag '{tag_name}' looking for '{end_tag_pattern}'.")


def update_blocks_after_processing(
    original_blocks: List[str],
    remaining_blocks_after_end: List[str],
    after_end_tag_content: str
) -> None:
    """Updates the original blocks list with unprocessed blocks and content."""
    original_blocks[:] = remaining_blocks_after_end
    if after_end_tag_content:
        original_blocks.insert(0, after_end_tag_content)
        
        