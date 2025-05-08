# django_spellbook/management/commands/processing/generator_utils.py

import os
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def remove_leading_dash(text: str) -> str:
    """Remove leading dash from text."""
    return text.lstrip('-')

def get_clean_url(url_pattern: str) -> str:
    """Create a clean URL from a pattern by removing leading dashes."""
    parts = url_pattern.split('/')
    clean_parts = [remove_leading_dash(part) for part in parts]
    return '/'.join(clean_parts)

def generate_view_name(url_pattern: str) -> str:
    """
    Generates a valid Python identifier for a view name from a URL pattern.

    Args:
        url_pattern: The URL pattern string.

    Returns:
        A valid Python identifier for the view name.
    """
    if not url_pattern: # should not happen
        print(f"Warning: Empty URL pattern detected. Returning 'view_'.")
        return "view_"
    # Replace slashes, hyphens, spaces, and periods with underscores
    view_name = re.sub(r"[/\s\-.]+", "_", url_pattern)

    # Remove any remaining characters that are not alphanumeric or underscore
    view_name = re.sub(r"[^\w]+", "", view_name)

    # Remove leading/trailing underscores
    view_name = view_name.strip("_")

    view_name = f"view_{view_name}"
    return _alter_first_digit(view_name)

def _alter_first_digit(text: str) -> str:
    """Alter the first digit found of a view_name, for use in generate_view_name."""
    # Ensure no leading digits (after prefixing) - crucial!
    try:
        if text[5].isdigit():  # Check the character *after* "view_"
            return f"view__{text[5:]}" # Add an extra underscore if it starts with a digit
        else:
            return text
    except IndexError: # if the string is too short, just return it
        print(f"Warning: view_name '{text}' is too short to be altered.")
        return text

def get_template_path(content_app: str, relative_url: str) -> str:
    """Generate template path from relative URL."""
    return os.path.join(content_app, 'spellbook_md', relative_url + '.html')

def get_spellbook_dir() -> str:
    """Get the django_spellbook base directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

def create_file_if_not_exists(file_path: str, content: str) -> None:
    """Create a file with initial content if it doesn't exist."""
    if not os.path.exists(file_path):
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            logger.debug(f"Created new file: {file_path}")
        except IOError as e:
            from django.core.management.base import CommandError
            raise CommandError(f"Failed to create {file_path}: {str(e)}")
            
def write_file(file_path: str, content: str) -> None:
    """Write content to a file, ensuring directory exists."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
    except IOError as e:
        from django.core.management.base import CommandError
        raise CommandError(f"Failed to write to {file_path}: {str(e)}")