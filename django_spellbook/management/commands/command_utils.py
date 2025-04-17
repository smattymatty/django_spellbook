# django_spellbook/management/commands/command_utils.py

import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path

from django.core.management.base import CommandError
from django.conf import settings

logger = logging.getLogger(__name__)

def normalize_settings(setting_path, setting_app):
    """Convert settings to normalized lists with backward compatibility."""
    md_paths = [setting_path] if isinstance(setting_path, (str, Path)) else setting_path
    md_apps = [setting_app] if isinstance(setting_app, str) else setting_app
    return md_paths, md_apps

def validate_spellbook_settings():
    """Validate required settings and support multiple source-destination pairs."""
    # Get settings values with backward compatibility
    md_path = getattr(settings, 'SPELLBOOK_MD_PATH', None)
    md_app = getattr(settings, 'SPELLBOOK_MD_APP', None)
    content_app = getattr(settings, 'SPELLBOOK_CONTENT_APP', None)
    
    # Prefer SPELLBOOK_MD_APP but fall back to SPELLBOOK_CONTENT_APP
    app_setting = md_app if md_app is not None else content_app
    
    if md_app is None and content_app is not None:
        logger.warning("SPELLBOOK_CONTENT_APP is deprecated, use SPELLBOOK_MD_APP instead.")
    
    # Normalize settings to lists
    md_file_paths, content_apps = normalize_settings(md_path, app_setting)
    
    # Validate settings
    _validate_setting_values(md_file_paths, content_apps)
    
    return md_file_paths, content_apps

def _validate_setting_values(md_file_paths, content_apps):
    """Validate setting values for correctness and compatibility."""
    # Check for missing settings
    missing_settings = []
    if not md_file_paths:
        missing_settings.append('SPELLBOOK_MD_PATH')
    if not content_apps:
        missing_settings.append('SPELLBOOK_MD_APP or SPELLBOOK_CONTENT_APP')
    
    if missing_settings:
        raise CommandError(f"Missing required settings: {', '.join(missing_settings)}")
    
    # Validate list lengths match
    if len(md_file_paths) != len(content_apps):
        raise CommandError("SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP must have the same number of entries")
    
    # Ensure each string is not empty
    for md_path in md_file_paths:
        if not md_path:
            raise CommandError("SPELLBOOK_MD_PATH must be a non-empty string.")
    for app_setting in content_apps:
        if not app_setting:
            raise CommandError("SPELLBOOK_MD_APP must be a non-empty string.")

def setup_directory_structure(content_app, dirpath):
    """Set up the necessary directory structure for content processing."""
    try:
        base_path = "/".join(dirpath.split("/")[:-1])
        content_app_path = os.path.join(base_path, content_app)

        if not os.path.exists(content_app_path):
            raise CommandError(f"Content app {content_app} not found in {base_path}")

        content_dir_path = content_app_path
        template_dir = setup_template_directory(content_dir_path, content_app)

        return content_dir_path, template_dir
    except Exception as e:
        raise CommandError(f"Could not set up content dir path: {str(e)}")

def setup_template_directory(content_dir_path, content_app):
    """Set up the template directory structure."""
    try:
        base_template_dir = Path(content_dir_path) / 'templates' / content_app / 'spellbook_md'
        base_template_dir.mkdir(parents=True, exist_ok=True)
        return str(base_template_dir)
    except Exception as e:
        raise CommandError(f"Could not create template directory: {str(e)}")

def get_folder_list(dirpath, md_file_path):
    """Get list of folders from dirpath relative to md_file_path."""
    logger.debug(f"Getting folder list for: {dirpath}")
    folder_split = dirpath.split("/")
    folder_list = []

    # trackers
    done = False
    n = -1
    while not done:
        dirname = folder_split[n]
        logger.debug(f"Processing dirname: {dirname}")
        if dirname == str(md_file_path).split("/")[-1]:
            done = True
            break
        else:
            folder_list.append(dirname)
            n -= 1

    logger.debug(f"Generated folder list: {folder_list}")
    return folder_list