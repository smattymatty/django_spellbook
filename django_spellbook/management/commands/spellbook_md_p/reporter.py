from typing import List, Tuple, Optional, Any
from io import StringIO
from django.core.management.base import OutputWrapper
from django.core.management.color import color_style

class MarkdownReporter:
    """
    Reporter class for Django Spellbook markdown processing.
    
    This class handles all reporting and output functionality related to the spellbook_md command,
    providing consistent formatting and organization of command outputs.
    """
    
    def __init__(self, stdout: Any, style=None):
        """
        Initialize the MarkdownReporter.
        
        Args:
            stdout: An output stream object (OutputWrapper from Django or another IO-like object)
            style: Django's style object from BaseCommand.style (if None, a default style will be created)
        """
        self.stdout = stdout
        # Use provided style or create a default one
        self.style = style or color_style()
        
    def generate_summary_report(self, pair_results: List[Tuple[str, str, str, bool, int]]):
        """
        Generate and display a summary report of the markdown processing results.
        
        Args:
            pair_results: List of tuples containing processing results for each source-destination pair.
                Each tuple contains:
                    - md_path (str): Path to the markdown source directory
                    - content_app (str): Name of the Django app where content was processed to
                    - url_prefix (str): URL prefix used for this content
                    - success (bool): Whether processing was successful
                    - processed_count (int): Number of files successfully processed
        """
        self.stdout.write("\nProcessing Summary:")
        success_count = sum(1 for _, _, _, success, _ in pair_results if success)
        total_processed = sum(count for _, _, _, success, count in pair_results if success)
        
        if success_count == len(pair_results):
            self.stdout.write(
                self.style.SUCCESS(
                    f"All {len(pair_results)} source-destination pairs processed successfully. "
                    f"Total files processed: {total_processed}."
                )
            )
        else:
            failed_pairs = [(src, dst, prefix) for src, dst, prefix, success, _ in pair_results if not success]
            message = (
                f"{success_count} of {len(pair_results)} pairs processed successfully. "
                f"Total files processed: {total_processed}. "
                f"Failed pairs: {', '.join(f'{src} → {dst} (prefix: {prefix})' for src, dst, prefix in failed_pairs)}"
            )
            self.stdout.write(self.style.WARNING(message))
        
    def error(self, message: str):
        """
        Display an error message with appropriate styling.
        
        Args:
            message: The error message to display
        """
        self.stdout.write(self.style.ERROR(message))
        
    def warning(self, message: str):
        """
        Display a warning message with appropriate styling.
        
        Args:
            message: The warning message to display
        """
        self.stdout.write(self.style.WARNING(message))
        
    def success(self, message: str):
        """
        Display a success message with appropriate styling.
        
        Args:
            message: The success message to display
        """
        self.stdout.write(self.style.SUCCESS(message))
        
    def write(self, message: str):
        """
        Display a plain message without special styling.
        
        Args:
            message: The message to display
        """
        self.stdout.write(message)