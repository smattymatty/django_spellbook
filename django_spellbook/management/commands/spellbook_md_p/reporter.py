from typing import List, Tuple, Optional, Any
from io import StringIO
from django.core.management.base import OutputWrapper

class MarkdownReporter:
    """
    Reporter class for Django Spellbook markdown processing.
    
    This class handles all reporting and output functionality related to the spellbook_md command,
    providing consistent formatting and organization of command outputs.
    """
    
    def __init__(self, stdout: Any):
        """
        Initialize the MarkdownReporter.
        
        Args:
            stdout: An output stream object (OutputWrapper from Django or another IO-like object)
        """
        self.stdout = stdout
        # Check if stdout has style attribute (Django's OutputWrapper does)
        self.has_style = hasattr(self.stdout, 'style')
        
    def _styled_write(self, text: str, style_method: Optional[str] = None):
        """
        Write text with the specified style if available, otherwise write plain text.
        
        Args:
            text: The text to write
            style_method: Name of the style method to use (e.g., 'SUCCESS', 'ERROR')
        """
        if self.has_style and style_method:
            style_func = getattr(self.stdout.style, style_method)
            self.stdout.write(style_func(text))
        else:
            # Fallback for stdout objects without style attribute
            self.stdout.write(text)
        
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
        
        The report includes:
            - Overall success/failure count
            - Total number of processed files
            - Details of any failed source-destination pairs
        """
        self.stdout.write("\nProcessing Summary:")
        success_count = sum(1 for _, _, _, success, _ in pair_results if success)
        total_processed = sum(count for _, _, _, success, count in pair_results if success)
        
        if success_count == len(pair_results):
            self._styled_write(
                f"All {len(pair_results)} source-destination pairs processed successfully. "
                f"Total files processed: {total_processed}.",
                "SUCCESS"
            )
        else:
            # Use exactly the same format string as the original to pass tests
            failed_pairs = [(src, dst, prefix) for src, dst, prefix, success, _ in pair_results if not success]
            message = (
                f"{success_count} of {len(pair_results)} pairs processed successfully. "
                f"Total files processed: {total_processed}. "
                f"Failed pairs: {', '.join(f'{src} → {dst} (prefix: {prefix})' for src, dst, prefix in failed_pairs)}"
            )
            self._styled_write(message, "WARNING")
        
    def error(self, message: str):
        """
        Display an error message with appropriate styling.
        
        Args:
            message: The error message to display
        """
        self._styled_write(message, "ERROR")
        
    def warning(self, message: str):
        """
        Display a warning message with appropriate styling.
        
        Args:
            message: The warning message to display
        """
        self._styled_write(message, "WARNING")
        
    def success(self, message: str):
        """
        Display a success message with appropriate styling.
        
        Args:
            message: The success message to display
        """
        self._styled_write(message, "SUCCESS")
        
    def write(self, message: str):
        """
        Display a plain message without special styling.
        
        Args:
            message: The message to display
        """
        self._styled_write(message)