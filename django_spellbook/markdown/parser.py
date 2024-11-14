from .extensions.django_like import DjangoLikeTagExtension
from ..blocks import SpellBlockRegistry
from typing import Dict, Any, Optional, List, Tuple
from django.template.loader import render_to_string
import re

import markdown
import logging

logger = logging.getLogger(__name__)


class MarkdownParser:
    """
    A parser that processes markdown text with custom spell blocks and extensions.

    This parser first processes any spell blocks in the text, then applies markdown
    formatting with additional extensions including Django-like template tags.

    Attributes:
        markdown_text (str): The original markdown text to be processed
        processed_text (str): The text after spell block processing
        html (str): The final HTML output after all processing
    """

    def __init__(self, markdown_text: str):
        """
        Initialize the parser with markdown text.

        Args:
            markdown_text (str): The markdown text to be processed
        """
        self.markdown_text = markdown_text
        # First process the blocks
        block_processor = BlockProcessor(self.markdown_text)
        self.processed_text = block_processor.process()
        # Then process the markdown with the processed blocks
        self.html = markdown.markdown(
            self.processed_text,
            extensions=[
                DjangoLikeTagExtension(),
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
            ],
        )

    def get_html(self) -> str:
        """
        Get the processed HTML content.

        Returns:
            str: The final HTML output
        """
        return self.html

    def get_markdown(self) -> str:
        """
        Get the original markdown content.

        Returns:
            str: The original markdown text
        """
        return self.markdown_text


class BlockProcessor:
    """
    Processes custom spell blocks within markdown content.

    This processor handles the parsing and rendering of spell blocks, which are
    special syntax elements enclosed in {~ ~} tags. It preserves code blocks
    and processes spell blocks only in non-code segments.

    Attributes:
        content (str): The original content to process
        pattern (Pattern): The regex pattern for matching spell blocks
        markdown_extensions (List[str]): List of markdown extensions to apply
    """

    def __init__(self, content: str):
        """
        Initialize the block processor.

        Args:
            content (str): The content to process
        """
        self.content = content
        self.pattern = re.compile(
            r'{~\s*(\w+)(?:\s+([^~]*?))?\s*~}(.*?){~~}', re.DOTALL)
        self.markdown_extensions = [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            DjangoLikeTagExtension()
        ]

    def process(self) -> str:
        """
        Process the content and render all spell blocks.

        Returns:
            str: The processed content with rendered spell blocks
        """
        try:
            segments = self._split_into_segments()
            return self._process_segments(segments)
        except Exception as e:
            logger.error(f"Error in block processing: {str(e)}")
            return self.content

    def _split_into_segments(self) -> List[Tuple[bool, str]]:
        """
        Split content into code and non-code segments.

        Returns:
            List[Tuple[bool, str]]: List of tuples containing (is_code_block, content)
        """
        segments: List[Tuple[bool, str]] = []
        is_code_block = False
        current_segment = ""

        for line in self.content.split('\n'):
            if line.strip().startswith('```'):
                segments.append((is_code_block, current_segment))
                current_segment = line + '\n'
                is_code_block = not is_code_block
            else:
                current_segment += line + '\n'

        segments.append((is_code_block, current_segment))
        return segments

    def _process_segments(self, segments: List[Tuple[bool, str]]) -> str:
        """
        Process each segment based on its type.

        Args:
            segments (List[Tuple[bool, str]]): List of (is_code, content) tuples

        Returns:
            str: The processed content with all segments combined
        """
        processed_segments = []
        for is_code, segment in segments:
            if is_code:
                processed_segments.append(segment)
            else:
                processed_segments.append(self._process_spell_blocks(segment))
        return "".join(processed_segments)

    def _process_spell_blocks(self, segment: str) -> str:
        """
        Process all spell blocks within a non-code segment.

        Args:
            segment (str): The segment to process

        Returns:
            str: The processed segment with rendered spell blocks
        """
        while True:
            match = self.pattern.search(segment)
            if not match:
                break

            processed_block = self._handle_block_match(match)
            segment = segment.replace(match.group(0), processed_block)

        return segment

    def _handle_block_match(self, match) -> str:
        """
        Process an individual block match.

        Args:
            match: The regex match object containing block information

        Returns:
            str: The rendered block content or error message
        """
        try:
            block_name = match.group(1)
            args_str = match.group(2) or ''
            block_content = match.group(3).strip()

            block_class = SpellBlockRegistry.get_block(block_name)
            if not block_class:
                logger.warning(f"Block '{block_name}' not found in registry")
                return f"<!-- Block '{block_name}' not found -->"

            return self._render_block(block_class, args_str, block_content)
        except Exception as e:
            logger.error(f"Error handling block match: {str(e)}")
            return f"<!-- Error processing block: {str(e)} -->"

    def _render_block(self, block_class, args_str: str, block_content: str) -> str:
        """
        Render a single block with its content.

        Args:
            block_class: The block class to instantiate
            args_str (str): The string containing block arguments
            block_content (str): The content inside the block

        Returns:
            str: The rendered block content or error message
        """
        try:
            kwargs = self._parse_block_args(args_str)

            block_instance = block_class(
                content=block_content,
                **kwargs
            )

            return block_instance.render()
        except Exception as e:
            logger.error(f"Error rendering block: {str(e)}")
            return f"<!-- Error rendering block: {str(e)} -->"

    def _parse_block_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse block arguments string into a dictionary.

        Args:
            args_str (str): The string containing block arguments

        Returns:
            Dict[str, Any]: Dictionary of parsed arguments
        """
        try:
            if not args_str:
                return {}

            kwargs: Dict[str, Any] = {}
            pattern = r'(\w+)=(?:"([^"]*?)"|\'([^\']*?)\'|(\S+))'

            # Validate the argument string format
            if not re.match(r'^(\s*\w+=(("[^"]*?")|(\'{1}[^\']*?\')|(\S+))\s*)*$', args_str):
                logger.error(f"Invalid argument format: {args_str}")
                return {}

            matches = re.finditer(pattern, args_str)
            for match in matches:
                key = match.group(1)
                # Get the first non-None value from the capturing groups
                value = next(v for v in match.groups()[1:] if v is not None)
                kwargs[key] = value

            return kwargs
        except Exception as e:
            logger.error(f"Error parsing block arguments: {str(e)}")
            return {}
