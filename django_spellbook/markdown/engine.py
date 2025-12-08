# django_spellbook/markdown/engine.py
import textwrap
from django.conf import settings
import markdown
import logging
import re
from re import Match
from typing import List, Tuple, Dict, Any, Optional, Type
#StringIO
from io import StringIO
from django.template.exceptions import TemplateDoesNotExist

# Assuming SpellBlockBase and SpellBlockRegistry are defined elsewhere,
# e.g., in django_spellbook.blocks
from django_spellbook.blocks import SpellBlockRegistry, BasicSpellBlock
from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter
from django_spellbook.markdown.extensions.list_aware_nl2br import ListAwareNl2BrExtension
from django_spellbook.markdown.preprocessors.list_fixer import ListFixerExtension
from django_spellbook.management.commands.spellbook_md_p.discovery import discover_blocks
from django_spellbook.markdown.attribute_parser import parse_spellblock_style_attributes


logger = logging.getLogger(__name__) # Standard Python logger

# --- Pre-compiled Regular Expressions ---
# This pattern is for initial block detection. It's known to have limitations
# with nesting and self-closing tags, which will be addressed by dedicated
# block locator/parser logic in future refactoring steps.
SPELLBLOCK_PATTERN = re.compile(
    # ~~~~~~ Block Name ~~~~~~    ~~~~~ Arguments (Optional) ~~~~~~~   ~ Content ~   ~End~
    r'{~\s*(\w+)\s*([^~]*?)\s*~}(.*?)(?:{~~})',  # Non-greedy args, content until {~~}
    re.DOTALL | re.IGNORECASE  # DOTALL for multiline content, IGNORECASE for block names
)
# Simpler pattern for self-closing blocks (conceptual, needs refinement in locator)
SPELLBLOCK_SELF_CLOSING_PATTERN = re.compile(
    r'{~\s*(\w+)\s*([^~]*?)\s*/~}', # Ends with /~}
    re.DOTALL | re.IGNORECASE
)

# Pattern for identifying fenced code blocks (```)
CODE_FENCE_PATTERN = re.compile(r'^```')

# Pattern for parsing key-value arguments within a SpellBlock tag
# Handles: key="value", key='value', key=value_without_quotes
ARGUMENT_PARSER_PATTERN = re.compile(r'(\w+)=(?:"([^"]*?)"|\'([^\']*?)\'|([^\s"\'=<>`]+))')


class SpellbookMarkdownEngine:
    """
    Core engine for parsing markdown text containing Django Spellbook's SpellBlocks.

    This engine orchestrates the process of:
    1. Identifying and extracting SpellBlocks from raw markdown text.
    2. Processing and rendering each SpellBlock using registered block classes.
    3. Converting the remaining markdown (now interspersed with rendered SpellBlock HTML)
       into final HTML using the python-markdown library and configured extensions.

    The engine is designed to be testable and extensible, providing a foundation
    for more advanced parsing features and SpellBlock capabilities.
    """

    def __init__(
        self,
        reporter: Optional[MarkdownReporter] = None,
        db_handler: Optional[Any] = None,  # Placeholder for future database interactions
        markdown_extensions: Optional[List[Any]] = None, # Can take Extension instances too
        fail_on_error: bool = False
    ):
        """
        Initializes the SpellbookMarkdownEngine.

        Args:
            reporter (Optional[MarkdownReporter]): An instance for reporting
                events, warnings, and errors during parsing. If None, a default
                MarkdownReporter instance will be created.
            db_handler (Optional[Any]): A placeholder for a future database
                interaction handler or context. Currently unused but anticipated for
                SpellBlocks that interact with Django models.
            markdown_extensions (Optional[List[Any]]): A list of
                python-markdown extension names (strings) or Extension instances.
                Defaults to a standard set including DjangoLikeTagExtension if None.
            fail_on_error (bool): If True, parsing errors may raise exceptions.
                If False (default), errors are reported and a fallback (e.g.,
                an HTML comment) is inserted into the output.
        """
        self.reporter: MarkdownReporter = reporter if reporter is not None else MarkdownReporter(
            stdout=StringIO(), style=None, report_level='minimal', report_format='text', report_output=None
        )
        self.db_handler: Optional[Any] = db_handler
        self.fail_on_error: bool = fail_on_error
        
        blocks = discover_blocks(self.reporter)
        
        reporter.write(f"SpellbookMarkdownEngine: Found {blocks} blocks.", level='debug')

        if markdown_extensions is None:
            self.markdown_extensions: List[Any] = [
                ListFixerExtension(),  # Preprocessor: adds blank lines before lists
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                ListAwareNl2BrExtension(),
                # Note: sane_lists removed to allow lists without blank lines before them
                'markdown.extensions.footnotes',
                'markdown.extensions.attr_list',
                'markdown.extensions.toc',
            ]
        else:
            self.markdown_extensions = markdown_extensions

        logger.debug(f"SpellbookMarkdownEngine initialized with extensions: {self.markdown_extensions}")

    def _split_markdown_by_code_fences(self, markdown_text: str) -> List[Tuple[str, bool]]:
        """
        Splits markdown text into segments, distinguishing code blocks from other content.
        SpellBlocks within fenced code blocks (```) should not be processed.

        Args:
            markdown_text (str): The raw markdown input string.

        Returns:
            List[Tuple[str, bool]]: A list of (segment_text, is_code_block) tuples.
        """
        segments: List[Tuple[str, bool]] = []
        lines = markdown_text.splitlines(keepends=True)
        in_code_block = False
        current_segment_lines: List[str] = []

        for line in lines:
            if CODE_FENCE_PATTERN.match(line.strip()): # Check for ```
                if current_segment_lines: # Finalize previous segment
                    segments.append(("".join(current_segment_lines), in_code_block))
                    current_segment_lines = []
                in_code_block = not in_code_block # Toggle state
                current_segment_lines.append(line) # Current line is part of the new segment state
            else:
                current_segment_lines.append(line)

        if current_segment_lines: # Append any remaining segment
            segments.append(("".join(current_segment_lines), in_code_block))
        
        logger.debug(f"Split markdown into {len(segments)} segments (code/non-code).")
        return segments

    def _parse_spellblock_arguments(self, raw_args_str: str) -> Dict[str, str]:
        """
        Parses a raw string of SpellBlock arguments into a dictionary using a utility function.
        """
        kwargs = parse_spellblock_style_attributes(raw_args_str, self.reporter)
        

        logger.debug(f"Parsed arguments from '{raw_args_str}' (via util): {kwargs}")
        return kwargs

    def _process_single_spellblock(
        self,
        block_name: str,
        raw_args_str: str,
        raw_content: str,
        is_self_closing: bool
    ) -> str:
        """
        Processes a single identified SpellBlock.

        Instantiates the appropriate SpellBlock class, passes arguments and content,
        and calls its render method.

        Args:
            block_name (str): The name of the SpellBlock (e.g., "alert").
            raw_args_str (str): The raw string of arguments.
            raw_content (str): The raw string content from within the SpellBlock.
                               For self-closing blocks, this will be empty or None.
            is_self_closing (bool): True if the block was identified as self-closing.

        Returns:
            str: The rendered HTML of the SpellBlock, or an HTML comment
                 indicating an error if processing fails.
        """
        self.reporter.write(f"Processing SpellBlock: {block_name}", level='debug')
        logger.debug(f"Attempting to process SpellBlock: {block_name}, Args: '{raw_args_str}', Self-closing: {is_self_closing}")

        BlockClass = SpellBlockRegistry.get_block(block_name)
        if not BlockClass:
            msg = f"SpellBlock type '{block_name}' not found in registry."
            self.reporter.error(msg)
            logger.warning(msg)
            return f""

        parsed_args = self._parse_spellblock_arguments(raw_args_str)

        # Content for self-closing blocks is typically None or empty.
        # For content-wrapping blocks, pass the raw_content; the block itself
        # can decide if/how to process it further (e.g., nested markdown parsing).
        content_for_block = "" if is_self_closing else raw_content
        
        block_instance = BlockClass(
            reporter=self.reporter,
            content=content_for_block,
            spellbook_parser=self, # Pass engine for potential nested parsing
            **parsed_args
        )

        rendered_html_from_block = block_instance.render()
        
        # --- ENGINE-LEVEL POST-PROCESSING ---
        # Strip leading/trailing whitespace from the whole block first
        processed_html = rendered_html_from_block.strip()
        # Dedent to remove common leading whitespace from each line
        # This helps prevent Markdown from interpreting indented HTML lines as code blocks
        if '\n' in processed_html: # Only dedent if there are multiple lines
            processed_html = "\n".join(line.lstrip() for line in rendered_html_from_block.splitlines())
        # --- END POST-PROCESSING ---

        if block_name == "argstest": # Your existing debug print
            print(f"\nDEBUG ENGINE: Raw HTML from '{block_name}.render()':")
            print("----------------RAW--------------------")
            print(rendered_html_from_block) # Show original
            print("----------------PROCESSED FOR INSERTION----------------")
            print(processed_html) # Show what will be used
            print("------------------------------------\n")

        logger.debug(f"Successfully rendered SpellBlock: {block_name}")
        return processed_html

    def _process_spellblocks_in_segment(self, markdown_segment: str) -> str:
        """
        Finds and processes all SpellBlocks within a given non-code markdown segment.

        This is a placeholder for the more advanced `spellblock_locator.py` logic.
        The current version uses a simple iterative regex replace which has known
        limitations with nesting and accurately identifying block boundaries.

        Args:
            markdown_segment (str): A segment of markdown text.

        Returns:
            str: The segment with top-level SpellBlocks rendered.
        """
        # This method needs to be entirely rewritten to support true nesting.
        # For now, it's a simplified loop similar to the original to get basic functionality.
        # A proper implementation would involve:
        # 1. Finding all top-level SpellBlock start/end tags.
        # 2. For each block, recursively calling a processing function for its *content*.
        # This ensures inner blocks are processed before outer ones are finalized.

        # Simple iterative replacement (will NOT handle nesting correctly)
        # This is a deliberate simplification for the *initial structural refactor*.
        # The GitHub issue "Refactor BlockProcessor for True Nested SpellBlock Parsing"
        # will address this directly.
        
        # First, handle self-closing blocks
        def replace_self_closing(match_obj):
            block_name = match_obj.group(1)
            raw_args_str = match_obj.group(2) or ''
            # _process_single_spellblock now returns cleaned (stripped, lstripped lines) HTML
            block_html = self._process_single_spellblock(block_name, raw_args_str, "", True)
            
            if block_html.strip(): # If the block rendered something meaningful
                # Ensure it's treated as a distinct block by the final Markdown pass
                return f"\n\n{block_html}\n\n"
            return "" # If block produced no output (e.g., error or truly empty render)

        processed_segment = SPELLBLOCK_SELF_CLOSING_PATTERN.sub(replace_self_closing, markdown_segment)

        # Then, handle content-wrapping blocks on the result
        temp_segment = processed_segment
        
        last_match_end = 0
        new_segments_list = []

        for match in SPELLBLOCK_PATTERN.finditer(temp_segment):
            # Add text before this match
            new_segments_list.append(temp_segment[last_match_end:match.start()])

            block_name = match.group(1)
            raw_args_str = match.group(2) or '' # Should be match.group(2)
            raw_content = match.group(3) or ''  # Should be match.group(3)
            
            block_html = self._process_single_spellblock(block_name, raw_args_str, raw_content, False)
            
            if block_html.strip():
                new_segments_list.append(f"\n\n{block_html}\n\n")
            # else: if block is empty, we effectively remove it and add nothing here.
            
            last_match_end = match.end()
        
        # Add any remaining text after the last match
        new_segments_list.append(temp_segment[last_match_end:])
        
        processed_segment = "".join(new_segments_list)
        
        return processed_segment

    def parse_and_render(self, markdown_text: str) -> str:
        """
        Parses the full markdown text, processes all SpellBlocks, and renders to HTML.

        This is the primary public method for using the engine to convert
        Spellbook-flavored markdown into HTML.

        Args:
            markdown_text (str): The raw markdown string to process.

        Returns:
            str: The final HTML output.
        """
        self.reporter.write(
            f"SpellbookMarkdownEngine: Starting parsing for text of length {len(markdown_text)}.",
            level='debug'
            )
        
        segments = self._split_markdown_by_code_fences(markdown_text)
        
        processed_segments_content: List[str] = []
        for content, is_code_block in segments:
            if is_code_block:
                logger.debug("Passing through code block segment unchanged.")
                processed_segments_content.append(content)
            else:
                logger.debug("Processing non-code segment for SpellBlocks.")
                processed_text_segment = self._process_spellblocks_in_segment(content)
                processed_segments_content.append(processed_text_segment)
        
        # Join segments. Using splitlines/join might be safer than simple string joining
        # if original line endings matter for python-markdown.
        # However, for this context, simple join is usually fine.
        text_with_rendered_spellblocks = "".join(processed_segments_content)
        logger.debug("All segments processed for SpellBlocks.")

        # Final conversion of the (now modified) markdown to HTML
        final_html = markdown.markdown(
            text_with_rendered_spellblocks,
            extensions=self.markdown_extensions,
            # output_format="html5" # Consider for modern HTML output
        )
        self.reporter.success("SpellbookMarkdownEngine: Markdown to HTML conversion complete.")
        logger.info("Successfully converted processed markdown to HTML.")
        return final_html
        

    # --- Placeholder for Database Interaction Logic ---
    def process_spellblocks_for_database(self, markdown_text: str) -> List[Any]:
        """
        (Future Implementation - Placeholder)
        Parses markdown to identify SpellBlocks requiring database interactions
        (e.g., `{~ question ~}`) and processes them (e.g., creates/updates models).

        This method would typically be called by the `spellbook_md` command *before*
        the HTML rendering pass if blocks need to write to DB and then potentially
        have their output affected by that DB state.

        Args:
            markdown_text (str): The raw markdown string.

        Returns:
            List[Any]: A list of results or identifiers from DB interactions.
                       The exact nature of this return value is TBD.
        """
        if self.db_handler: # pragma: no cover
            # TODO: Implement database interactions
            logger.info("DB handler present, but database-specific SpellBlock processing is not yet implemented in the engine.")
            # Conceptual:
            # 1. Use a robust block locator to find all SpellBlock instances (name, args, content).
            # 2. For each located block:
            #    block_class = SpellBlockRegistry.get_block(name)
            #    if block_class and hasattr(block_class, 'save_to_db'):
            #        instance = block_class(content=..., reporter=..., spellbook_parser=self, **args)
            #        instance.save_to_db(self.db_handler, source_file_context=...)
        else: # pragma: no cover
            logger.warning("No database handler configured; cannot perform database-specific SpellBlock processing.")
        return [] # pragma: no cover

# --- Test Code ---

if __name__ == '__main__':
    try:
        from django.conf import settings as django_settings
        if not django_settings.configured:
            django_settings.configure(
                INSTALLED_APPS=[
                    'django_spellbook',
                ],
                TEMPLATES=[
                    {
                        'BACKEND': 'django.template.backends.django.DjangoTemplates',
                        'DIRS': [],
                        'APP_DIRS': True,
                        'OPTIONS': {
                            'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                            ],
                        },
                    },
                ],
            )
        import django
        django.setup() # Initializes the app registry, among other things.
    except Exception as e:
        print(f"WARNING: Minimal Django setup for __main__ failed: {e}")
    # --- End Minimal Django Setup ---  
    debug_reporter = MarkdownReporter(
        stdout=StringIO(), style=None, report_level='debug', report_format='text', report_output=None
    )

    new_engine = SpellbookMarkdownEngine(reporter=debug_reporter)

    test_markdown_content = """
# Test Document

This is a test of the `SpellbookMarkdownEngine`.

{~ quote author="A Wizard" ~}

Magic is programming by other means.
{~~}

Here is a card:

{~ card title="My Test Card" class="custom-card-style" ~}

This card contains some **bold** and _italic_ text.
And a list:

- Item 1
- Item 2
{~~}

{~ alert type="danger" ~}
DANGER! You are about to enter a dangerous area.
{~~}
"""

    rendered_html = new_engine.parse_and_render(test_markdown_content)
    print(rendered_html)