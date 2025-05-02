import os
import datetime
import logging
import traceback
from typing import List, Dict, Optional, Any

from django.core.management.base import CommandError
from django_spellbook.markdown.context import SpellbookContext
from django_spellbook.management.commands.processing.file_processor import ProcessedFile
from django_spellbook.management.commands.processing.generator_utils import (
    remove_leading_dash,
    get_clean_url,
    generate_view_name,
    get_template_path
)

logger = logging.getLogger(__name__)

class ViewGenerator:
    """
    Handles view function generation for markdown-generated content.
    """
    
    def __init__(self, content_app: str):
        """
        Initialize view generator.
        
        Args:
            content_app: Django app name where content will be stored
        """
        if not content_app or not isinstance(content_app, str):
            raise CommandError("Content app name must be a non-empty string")
        self.content_app = content_app
    
    def generate_view_functions(self, processed_files: List[ProcessedFile]) -> List[str]:
        """
        Generate view functions for the processed files.
        
        Args:
            processed_files: List of processed markdown files
            
        Returns:
            List of view function strings
        """
        if not processed_files:
            logger.warning("No processed files provided to generate view functions")
            return []
            
        view_functions = []
        
        for i, processed_file in enumerate(processed_files):
            try:
                if not isinstance(processed_file, ProcessedFile):
                    logger.warning(f"Item {i} is not a ProcessedFile, skipping")
                    continue
                    
                view_function = self._generate_view_function(processed_file)
                view_functions.append(view_function)
            except Exception as e:
                file_path = getattr(processed_file, 'original_path', f"file #{i}")
                logger.error(f"Error generating view function for {file_path}: {str(e)}")
                logger.debug(traceback.format_exc())
                # Continue processing other files rather than failing completely
        
        if not view_functions:
            logger.warning("No view functions were generated from the provided files")
            
        return view_functions
    
    def _generate_view_function(self, processed_file: ProcessedFile) -> str:
        """
        Generate view function for a single file.
        
        Args:
            processed_file: Processed markdown file
            
        Returns:
            View function string
        """
        try:
            self.validate_required_attributes(processed_file)
            
            view_name = generate_view_name(remove_leading_dash(processed_file.relative_url))
            if not view_name:
                raise ValueError(f"Could not generate valid view name from URL: {processed_file.relative_url}")
                
            template_path = get_template_path(self.content_app, processed_file.relative_url)
            clean_url = get_clean_url(processed_file.relative_url)
                
            # Create metadata dictionary
            metadata = self._prepare_metadata(processed_file)
            metadata_repr = self.convert_metadata_to_string(metadata)
            
            context_dict = self._prepare_context_dict(processed_file.context)
            try:
                # Test representation for syntax/injection issues
                context_str = repr(context_dict)
                
                self.check_for_dangerous_content(context_str)
                        
            except Exception as e:
                logger.error(f"Context dictionary security validation failed: {str(e)}")
                # Use a fallback empty context for safety
                context_dict = {}
        
            
            return f"""
def {view_name}(request):
    context = {context_dict}
    context['toc'] = TOC 
    context['current_url'] = '{clean_url}'
    context['metadata'] = {metadata_repr}
    return render(request, '{template_path}', context)
"""
        except Exception as e:
            # Convert all exceptions into CommandError with helpful message
            error_message = f"Failed to generate view function: {str(e)}"
            logger.error(error_message)
            logger.debug(traceback.format_exc())
            raise CommandError(error_message)
    
    def _safe_get_attr(self, obj, attr_name, default=None):
        """Safely get attribute from an object with a default fallback."""
        if obj is None:
            return default
        return getattr(obj, attr_name, default)
    
    def _prepare_metadata(self, processed_file: ProcessedFile) -> Dict[str, Any]:
        """
        Prepare metadata dictionary for a file.
        
        Args:
            processed_file: Processed markdown file
            
        Returns:
            Metadata dictionary
        """
        try:
            if ".." in str(processed_file.template_path):
                # If template path is outside of the app directory, raise an error
                raise ValueError(f"Template path is outside of the app directory: {processed_file.template_path}")
            # Extract path parts for title fallback
            path_parts = processed_file.relative_url.split('/')
            url_name = processed_file.relative_url.replace('/', '_')
            
            # If context has prepare_metadata method (new implementation), use it
            if (hasattr(processed_file, 'context') and processed_file.context and
                hasattr(processed_file.context, 'prepare_metadata') and 
                callable(processed_file.context.prepare_metadata)):
                
                try:
                    return processed_file.context.prepare_metadata(
                        self.content_app, 
                        processed_file.relative_url
                    )
                except Exception as e:
                    logger.warning(f"Error using context.prepare_metadata: {str(e)}, falling back to direct implementation")
            
            # Safely get context attributes with fallbacks
            context = processed_file.context if hasattr(processed_file, 'context') else None
            
            # Build comprehensive metadata including namespace information
            metadata = {
                'title': self._safe_get_attr(context, 'title', path_parts[-1].replace('-', ' ').title()),
                'published': self._safe_get_attr(context, 'published', None),
                'modified': self._safe_get_attr(context, 'modified', None),
                'url_path': get_clean_url(processed_file.relative_url),
                'raw_content': self._safe_get_attr(context, 'raw_content', ''),
                'is_public': self._safe_get_attr(context, 'is_public', True),
                'tags': self._safe_get_attr(context, 'tags', []),
                'custom_meta': self._safe_get_attr(context, 'custom_meta', {}),
                'namespace': self.content_app,  # Add app namespace
                'url_name': url_name,  # Simple URL name
                'namespaced_url': f"{self.content_app}:{url_name}"  # Full namespaced URL
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error preparing metadata: {str(e)}")
            logger.debug(traceback.format_exc())
            # Return a minimal metadata dict if preparation fails
            return {
                'title': 'Error preparing metadata',
                'url_path': get_clean_url(processed_file.relative_url) if hasattr(processed_file, 'relative_url') else '',
                'namespace': self.content_app
            }
    
    def _prepare_context_dict(self, context: SpellbookContext) -> Dict[str, Any]:
        """
        Prepare context dictionary for template rendering.
        
        Args:
            context: SpellbookContext object
            
        Returns:
            Context dictionary
        """
        return context.to_dict()
    
    
    def check_for_dangerous_content(self, context_str: str):
        """
        Check for potentially dangerous patterns in context string.
        
        Args:
            context_str: String representation of context dictionary
            
        Raises:
            ValueError: If dangerous patterns are detected
        """
        dangerous_patterns = []
        
        # for pattern in dangerous_patterns:
        #     if pattern in context_str:
        #         raise ValueError(f"Potentially unsafe content detected in context: '{pattern}'")
            
            
    def validate_required_attributes(self, processed_file: ProcessedFile):
        """
        Validate required attributes for a ProcessedFile object.
        
        Args:
            processed_file: ProcessedFile object
            
        Raises:
            ValueError: If required attributes are missing
        """
        if not hasattr(processed_file, 'relative_url') or not processed_file.relative_url:
            raise ValueError("ProcessedFile missing relative_url attribute")
            
        if not hasattr(processed_file, 'context') or not processed_file.context:
            raise ValueError("ProcessedFile missing context attribute")
            
        # If context exists and has validate method, use it
        if processed_file.context and hasattr(processed_file.context, 'validate') and callable(processed_file.context.validate):
            try:
                validation_errors = processed_file.context.validate()
                # Explicitly check if validation_errors evaluates to True
                if validation_errors:
                    if isinstance(validation_errors, list) and len(validation_errors) > 0:
                        # Convert all items to strings before joining
                        errors_str = ', '.join(str(error) for error in validation_errors)
                        raise ValueError(f"Context validation failed: {errors_str}")
                    else:
                        # Handle non-list error output
                        raise ValueError(f"Context validation failed: {validation_errors}")
            except Exception as e:
                # Re-raise ValueError exceptions
                if isinstance(e, ValueError):
                    raise
                logger.warning(f"Error during context validation: {str(e)}")
        
    def convert_metadata_to_string(self, metadata: Dict[str, Any]):
        """
        Convert metadata dictionary to string representation for inclusion in the view.
        
        Args:
            metadata: Metadata dictionary
        Returns:
            String representation of metadata
        """
        # Convert metadata to string representation for inclusion in the view
        metadata_repr = "{\n"
        for k, v in metadata.items():
            metadata_repr += f"        '{k}': {repr(v)},\n"
        metadata_repr += "    }"
        
        return metadata_repr
    
    def _prepare_toc(self, context_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare TOC dictionary for template rendering.
        
        Args:
            context_dict: Context dictionary
        Returns:
            TOC dictionary
        """
        # Safely convert datetime objects to their representation
        result = {}
        for k, v in context_dict.items():
            try:
                if isinstance(v, (datetime.datetime, datetime.date)):
                    result[k] = repr(v)
                # if the toc isn't the correct format, raise an error
                elif k == 'toc' and not isinstance(v, dict):
                    raise ValueError(f"TOC is not a dictionary: {v}")
                else:
                    result[k] = v
            except ValueError:
                result[k] = None
                raise Exception(f"TOC is not a dictionary: {v}")
                
        return result