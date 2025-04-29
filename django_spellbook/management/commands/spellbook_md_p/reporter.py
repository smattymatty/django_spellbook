# django_spellbook/management/commands/spellbook_md_p/reporter.py
from typing import List, Tuple, Optional, Any, Dict
from io import StringIO
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style


class MarkdownReporter:
    """
    Reporter class for Django Spellbook markdown processing.
    
    This class handles all reporting and output functionality related to the spellbook_md command,
    providing consistent formatting and organization of command outputs.
    """
    
    def __init__(
        self, 
        stdout: Any, 
        style=None, 
        report_level: str = 'detailed', 
        report_format: str = 'text', 
        report_output: Optional[str] = None
    ):
        """
        Initialize the MarkdownReporter.
        
        Args:
            stdout: An output stream object (OutputWrapper from Django or another IO-like object)
            style: Django's style object from BaseCommand.style (if None, a default style will be created)
            report_level: Level of detail in the report ('minimal', 'detailed', or 'debug')
            report_format: Format of the report ('text', 'json', or 'none')
            report_output: File path to save the report (if None, print to stdout)
            
        attributes:
            stdout: An output stream object (OutputWrapper from Django or another IO-like object)
            style: Django's style object from BaseCommand.style (if None, a default style will be created)
            report_level: Level of detail in the report ('minimal', 'detailed', or 'debug')
            report_format: Format of the report ('text', 'json', or 'none')
            report_output: File path to save the report (if None, print to stdout)
            spellblocks: A list of SpellblockStatistics objects for each discovered spellblock
        """
        self.stdout = stdout
        self.style = style or color_style()
        self.report_level = report_level
        self.report_format = report_format
        self.report_output = report_output
        from django_spellbook.management.commands.spellbook_md_p.discovery import SpellblockStatistics
        self.spellblocks: List[SpellblockStatistics] = []
        
        # If report_output is specified, prepare the output file
        self.output_file = None
        if self.report_output and self.report_format != 'none':
            try:
                self.output_file = open(self.report_output, 'w', encoding='utf-8')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error opening output file: {str(e)}"))
                self.report_output = None  # Fallback to stdout
        
    def generate_summary_report(self, pair_results: List[Tuple[str, str, str, bool, int]]):
        """
        Generate and display a summary report of the markdown processing results.
        
        Args:
            pair_results: List of tuples containing processing results for each source-destination pair.
        """
        if self.report_format == 'none':
            return
            
        success_count = sum(1 for _, _, _, success, _ in pair_results if success)
        total_processed = sum(count for _, _, _, success, count in pair_results if success)
        failed_pairs = [(str(src), dst, prefix) for src, dst, prefix, success, _ in pair_results if not success]
        
        if self.report_format == 'json':
            self._generate_json_report(pair_results, success_count, total_processed, failed_pairs)
        else:  # Default to text format
            self._generate_text_report(pair_results, success_count, total_processed, failed_pairs)

    def _generate_text_report(
        self, 
        pair_results: List[Tuple[str, str, str, bool, int]],
        success_count: int,
        total_processed: int, 
        failed_pairs: List[Tuple[str, str, str]]
        ):
        """
        Generate a text report for human consumption. 
        Outputs to the console, or to a file if specified.
        
        Args:
            pair_results: List of tuples containing processing results for each source-destination pair
            success_count: Number of successful pairs
            total_processed: Total number of files processed
            failed_pairs: List of tuples containing failed source-destination pairs
        """
        # First, decide where to output
        output = self.output_file if self.output_file else self.stdout
        
        output.write("\nProcessing Summary:\n")
        message = "--SUMMARY REPORT--\n"
        if success_count == len(pair_results):
            message += (
                f"All {len(pair_results)} source-destination pairs processed successfully. "
                f"Total files processed: {total_processed}.\n"
            )
        else:
            message += (
                f"{success_count} of {len(pair_results)} pairs processed successfully. "
                f"Total files processed: {total_processed}.\n"
            )
            if failed_pairs:
                message += f"Failed pairs: {', '.join(f'{src} → {dst} (prefix: {prefix})' for src, dst, prefix in failed_pairs)}"
        # Add spellblock statistics to the report
        if self.spellblocks:
            message += "\n\nSpellblock Usage:\n"
            for block in self.spellblocks:
                message += f"- {block.name} -"
                message += "\n"
        else:
            message += "\nNo spellblocks were discovered during processing.\n"
        
        output.write(self.style.WARNING(message) if hasattr(output, 'write') else message)
        return message

    def _generate_json_report(
        self, 
        pair_results: List[Tuple[str, str, str, bool, int]],
        success_count: int,
        total_processed: int,
        failed_pairs: List[Tuple[str, str, str]]
        ):
        """
        Generate a JSON report. Outputs to the console, or to a file if specified.
        
        Args:
            pair_results: List of tuples containing processing results for each source-destination pair
            success_count: Number of successful pairs
            total_processed: Total number of files processed
            failed_pairs: List of tuples containing failed source-destination pairs
        """
        import json
        
        # Prepare the JSON data
        report_data = {
            "summary": {
                "total_pairs": len(pair_results),
                "successful_pairs": success_count,
                "total_processed_files": total_processed
            },
            "pairs": [
                {
                    "source": str(src),
                    "destination": dst,
                    "url_prefix": prefix,
                    "success": success,
                    "processed_files": count
                }
                for src, dst, prefix, success, count in pair_results
            ]
        }
        
        if failed_pairs:
            report_data["failed_pairs"] = [
                {"source": src, "destination": dst, "url_prefix": prefix}
                for src, dst, prefix in failed_pairs
            ]
        # Add spellblock statistics to the report
        if self.spellblocks:
            report_data["spellblocks"] = [
                {
                    "name": block.name,
                    'total_uses': block.total_uses,
                    'failed_uses': block.failed_uses
                }
                for block in self.spellblocks
            ]
        
        # Convert to JSON string
        json_str = json.dumps(report_data, indent=2)
        
        # Output to file or stdout
        output = self.output_file if self.output_file else self.stdout
        output.write(json_str)
        
        json_dict = json.loads(json_str)
        return json_dict

    def __del__(self):
        """Clean up resources when the reporter is destroyed."""
        if hasattr(self, 'output_file') and self.output_file:
            self.output_file.close()

        
    def _should_output(self, level: str) -> bool:
        """Determine if a message should be output based on the report level."""
        if self.report_format == 'none':
            return False
        
        levels = {'minimal': 0, 'detailed': 1, 'debug': 2}
        return levels.get(level, 1) <= levels.get(self.report_level, 1)

    def error(self, message: str):
        """Always display error messages regardless of report level."""
        if self.report_format == 'none':
            return
        self.stdout.write(self.style.ERROR(message))
        
    def warning(self, message: str, level: str = 'detailed'):
        """Display a warning message if the report level allows."""
        if not self._should_output(level):
            return
        self.stdout.write(self.style.WARNING(message))
        
    def success(self, message: str, level: str = 'detailed'):
        """Display a success message if the report level allows."""
        if not self._should_output(level):
            return
        self.stdout.write(self.style.SUCCESS(message))
        
    def write(self, message: str, level: str = 'detailed'):
        """Display a plain message if the report level allows."""
        if not self._should_output(level):
            return
        self.stdout.write(message)
        
    def record_spellblock_usage(self, block_name: str, success: bool = True):
        """
        Record usage of a spellblock in a file.
        
        Args:
            block_name: Name of the spellblock
            success: Whether the spellblock was used successfully
        """
        for block in self.spellblocks:
            if block.name == block_name:
                if success:
                    block.total_uses += 1
                else:
                    block.failed_uses += 1
                return
        
        # If we get here, the block wasn't found, so add it
        from django_spellbook.management.commands.spellbook_md_p.discovery import build_new_spellblock_statistics
        new_block = build_new_spellblock_statistics(block_name)
        new_block.total_files = 0
        if success:
            new_block.successful_files = 0
        else:
            new_block.failed_files = 0
        self.spellblocks.append(new_block)