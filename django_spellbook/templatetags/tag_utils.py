# django_spellbook/templatetags/tag_utils.py
import logging
from typing import List, Optional, Union
from pathlib import Path

from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger(__name__)

def get_metadata_template(display_type: str, app_index: int = 0) -> str:
    """
    Get the appropriate metadata template path based on display type and app index.
    
    Args:
        display_type (str): Either 'for_user' or 'for_dev'
        app_index (int): Index of the app in multi-app configurations
        
    Returns:
        str: Template path
    """
    if display_type not in ['for_user', 'for_dev']:
        raise ValueError(f"Invalid display_type: {display_type}. Must be 'for_user' or 'for_dev'")
    
    # Get the setting value with a fallback to None
    setting_name = 'SPELLBOOK_MD_METADATA_BASE'
    metadata_base_setting = getattr(settings, setting_name, None)
    
    # Default templates
    default_templates = {
        'for_user': 'django_spellbook/metadata/for_user.html',
        'for_dev': 'django_spellbook/metadata/for_dev.html'
    }
    
    # If setting is not provided, use defaults
    if metadata_base_setting is None:
        return default_templates[display_type]
    
    # If setting is a tuple, it applies to all apps
    if isinstance(metadata_base_setting, tuple) and len(metadata_base_setting) == 2:
        user_template, dev_template = metadata_base_setting
        return user_template if display_type == 'for_user' else dev_template
    
    # If setting is a list, it's per-app configuration
    if isinstance(metadata_base_setting, list):
        try:
            app_setting = metadata_base_setting[app_index]
            if isinstance(app_setting, tuple) and len(app_setting) == 2:
                user_template, dev_template = app_setting
                return user_template if display_type == 'for_user' else dev_template
            else:
                logger.warning(
                    f"Invalid {setting_name} format at index {app_index}. "
                    f"Expected tuple of (user_template, dev_template). "
                    f"Using default template."
                )
        except IndexError:
            logger.warning(
                f"App index {app_index} out of range for {setting_name}. "
                f"Using default template."
            )
    
    # Fallback to default if setting format is incorrect or index out of range
    logger.warning(
        f"Invalid {setting_name} format. Expected tuple of (user_template, dev_template) "
        f"or list of such tuples. Using default template."
    )
    return default_templates[display_type]

def get_user_metadata_template(app_index: int = 0) -> str:
    """
    Get the template path for user metadata.
    
    Args:
        app_index (int): Index of the app in multi-app configurations
        
    Returns:
        str: Template path for user metadata
    """
    return get_metadata_template('for_user', app_index)

def get_dev_metadata_template(app_index: int = 0) -> str:
    """
    Get the template path for developer metadata.
    
    Args:
        app_index (int): Index of the app in multi-app configurations
        
    Returns:
        str: Template path for developer metadata
    """
    return get_metadata_template('for_dev', app_index)

def get_current_app_index(context) -> int:
    """
    Determine the current app index from the context.
    
    Args:
        context: Template context
        
    Returns:
        int: App index (defaults to 0 if not determinable)
    """
    # Try to get app index from context
    # This assumes the context might have some app identification
    # Implement based on how app information is stored in context
    return getattr(context, 'app_index', 0)