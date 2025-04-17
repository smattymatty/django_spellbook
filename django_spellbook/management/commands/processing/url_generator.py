# django_spellbook/management/commands/processing/url_generator.py

import os
import logging
import traceback
from typing import List, Dict, Optional, Any

from django.core.management.base import CommandError
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.generator_utils import (
    remove_leading_dash,
    get_clean_url,
    generate_view_name
)

logger = logging.getLogger(__name__)

class URLGenerator:
    """
    Handles URL pattern generation for markdown-generated content.
    """
    
    def __init__(self, content_app: str):
        """
        Initialize URL generator.
        
        Args:
            content_app: Django app name where content will be stored
            
        Raises:
            CommandError: If content_app is invalid
        """
        if not content_app or not isinstance(content_app, str):
            raise CommandError("Content app name must be a non-empty string")
        
        self.content_app = content_app
    
    def generate_url_patterns(self, processed_files: List[ProcessedFile]) -> List[str]:
        """
        Generate URL patterns for the processed files.
        
        Args:
            processed_files: List of processed markdown files
            
        Returns:
            List of URL pattern strings
            
        Raises:
            CommandError: If there's an error generating URL patterns
        """
        if not processed_files:
            logger.warning("No processed files provided to generate URL patterns")
            return []
        
        url_patterns = []
        
        for i, processed_file in enumerate(processed_files):
            try:
                # Validate processed_file is the right type
                if not isinstance(processed_file, ProcessedFile):
                    logger.warning(f"Item {i} is not a ProcessedFile, skipping")
                    continue
                
                url_pattern = self._generate_url_pattern(processed_file)
                url_patterns.append(url_pattern)
            except Exception as e:
                file_path = getattr(processed_file, 'original_path', f"file #{i}")
                logger.error(f"Error generating URL pattern for {file_path}: {str(e)}")
                logger.debug(traceback.format_exc())
                # Continue processing other files rather than failing completely
        
        if not url_patterns:
            logger.warning("No URL patterns were generated from the provided files")
        
        # Validate all URL patterns before returning
        self._validate_url_patterns(url_patterns)
        
        return url_patterns
    
    def _validate_url_patterns(self, url_patterns: List[str]) -> None:
        """
        Validate a list of URL patterns for uniqueness and basic structure.
        
        Args:
            url_patterns: List of URL pattern strings
            
        Raises:
            CommandError: If there are validation issues with the URL patterns
        """
        # Check for duplicates (which would cause Django URL conflicts)
        url_names = {}
        url_paths = {}
        
        for pattern in url_patterns:
            try:
                # Extract path and name from pattern using simple parsing
                # Example: path('docs/guide/', docs_guide, name='docs_guide')
                parts = pattern.split("path('")
                if len(parts) != 2:
                    continue
                    
                path_part = parts[1].split("',")[0]
                
                name_parts = pattern.split("name='")
                if len(name_parts) != 2:
                    continue
                    
                name_part = name_parts[1].split("')")[0]
                
                # Check for duplicate paths
                if path_part in url_paths:
                    logger.warning(f"Duplicate URL path detected: '{path_part}' in '{pattern}' and '{url_paths[path_part]}'")
                    
                # Check for duplicate names
                if name_part in url_names:
                    logger.warning(f"Duplicate URL name detected: '{name_part}' in '{pattern}' and '{url_names[name_part]}'")
                
                url_paths[path_part] = pattern
                url_names[name_part] = pattern
                
            except Exception as e:
                logger.warning(f"Could not validate URL pattern '{pattern}': {str(e)}")
    
    def _generate_url_pattern(self, processed_file: ProcessedFile) -> str:
        """
        Generate URL pattern for a single file.
        
        Args:
            processed_file: Processed markdown file
            
        Returns:
            URL pattern string
            
        Raises:
            ValueError: If required attributes are missing or invalid
        """
        try:
            # Validate processed_file has required attributes
            if not hasattr(processed_file, 'relative_url') or not processed_file.relative_url:
                raise ValueError("ProcessedFile missing relative_url attribute")
            
            view_name = generate_view_name(remove_leading_dash(processed_file.relative_url))
            if not view_name:
                raise ValueError(f"Could not generate valid view name from URL: {processed_file.relative_url}")
            
            # Validate view name follows Python identifier rules
            if not view_name.isidentifier():
                raise ValueError(f"Generated view name '{view_name}' is not a valid Python identifier")
            
            # Python has a max identifier length (implementation-dependent)
            if len(view_name) > 100:  # Reasonable limit
                logger.warning(f"View name '{view_name}' is quite long ({len(view_name)} chars)")
                
            clean_url = get_clean_url(processed_file.relative_url)
            
            # Validate clean_url doesn't contain dangerous characters
            if not self._is_safe_url(clean_url):
                raise ValueError(f"Invalid URL path detected: {clean_url}")
            
            # Create a URL name using the full path (for reverse lookup)
            url_name = clean_url.replace('/', '_')
            
            # Check if URL name is valid
            if not url_name or not url_name[0].isalpha() and url_name[0] != '_':
                raise ValueError(f"Generated URL name '{url_name}' is not valid")
            
            pattern = f"path('{clean_url}/', {view_name}, name='{url_name}')"
            
            # Log the generated pattern at debug level
            logger.debug(f"Generated URL pattern: {pattern}")
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error in _generate_url_pattern: {str(e)}")
            logger.debug(traceback.format_exc())
            raise ValueError(f"Failed to generate URL pattern: {str(e)}")
        
    # Extend URL path validation to catch more problematic patterns
    def _is_safe_url(self, url: str) -> bool:
        """Check if a URL is safe from common attacks."""
        dangerous_patterns = [
            '..',     # Directory traversal
            '//',     # Protocol confusion
            '\x00',   # Null byte (can cause issues in some systems)
            '<?',     # PHP tags
            '%',      # URL encoding can sometimes be used to bypass filters
        ]
        return not any(pattern in url for pattern in dangerous_patterns)