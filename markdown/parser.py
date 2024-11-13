from .extensions.django_like import DjangoLikeTagExtension
from ..blocks import SpellBlockRegistry
from typing import Dict, Any, Optional, List, Tuple
from django.template.loader import render_to_string
import re

import markdown
import logging

logger = logging.getLogger(__name__)


class MarkdownParser:
    def __init__(self, markdown_text: str):
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
        return self.html

    def get_markdown(self) -> str:
        return self.markdown_text


class BlockProcessor:
    def __init__(self, content: str):
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
        """Main processing method"""
        try:
            segments = self._split_into_segments()
            return self._process_segments(segments)
        except Exception as e:
            logger.error(f"Error in block processing: {str(e)}")
            return self.content

    def _split_into_segments(self) -> List[Tuple[bool, str]]:
        """Split content into code and non-code segments"""
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
        """Process each segment based on its type"""
        processed_segments = []
        for is_code, segment in segments:
            if is_code:
                processed_segments.append(segment)
            else:
                processed_segments.append(self._process_spell_blocks(segment))
        return "".join(processed_segments)

    def _process_spell_blocks(self, segment: str) -> str:
        """Process spell blocks within a non-code segment"""
        while True:
            match = self.pattern.search(segment)
            if not match:
                break

            processed_block = self._handle_block_match(match)
            segment = segment.replace(match.group(0), processed_block)

        return segment

    def _handle_block_match(self, match) -> str:
        """Process individual block matches"""
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
        """Render a single block with its content"""
        try:
            kwargs = self._parse_block_args(args_str)

            # Create block instance with raw content
            block_instance = block_class(
                content=block_content,  # Pass raw content
                **kwargs
            )

            # Let the block handle its own rendering
            return block_instance.render()
        except Exception as e:
            logger.error(f"Error rendering block: {str(e)}")
            return f"<!-- Error rendering block: {str(e)} -->"

    def _parse_block_args(self, args_str: str) -> Dict[str, Any]:
        """Parse block arguments string into dictionary"""
        try:
            if not args_str:
                return {}

            kwargs: Dict[str, Any] = {}
            pattern = r'(\w+)=(?:"([^"]*?)"|\'([^\']*?)\'|(\S+))'
            matches = re.finditer(pattern, args_str)

            for match in matches:
                key = match.group(1)
                value = next(v for v in match.groups()[1:] if v is not None)
                kwargs[key] = value

            return kwargs
        except Exception as e:
            logger.error(f"Error parsing block arguments: {str(e)}")
            return {}
