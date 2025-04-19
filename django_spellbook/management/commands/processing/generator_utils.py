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
    """Generate a valid Python identifier for a view name from a URL pattern."""
    # Split by slashes first to handle each path component separately
    parts = url_pattern.split('/')
    
    # Process each part to clean dashes
    cleaned_parts = []
    for part in parts:
        # Remove leading dashes and replace internal dashes with underscores
        cleaned_part = part.lstrip('-')
        cleaned_part = cleaned_part.replace('-', '_')
        cleaned_parts.append(cleaned_part)
    
    # Join with underscores (replacing slashes with underscores)
    view_name = '_'.join(cleaned_parts)
    view_name = f"view_{view_name}"
    view_name = view_name.replace('.', '-')
    
    return view_name

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