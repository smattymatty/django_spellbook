# django_spellbook/management/commands/command_utils.py

import os
import logging
from typing import List, Tuple, Optional, IO, Set
from pathlib import Path

from django.core.management.base import CommandError
from django.conf import settings

logger = logging.getLogger(__name__)

def normalize_settings(setting_path, setting_app, setting_base_template):
    """
    Convert settings to normalized lists with backward compatibility.
    
    Args:
        setting_path: Path to markdown files.
        setting_app: Name of the content app.
        setting_base_template: Base template or list of base templates.
    
    Returns:
        Tuple[List[str], List[str], List[Optional[str]]]: md_paths, md_apps, and base_templates.
    """
    md_paths: List[str] = [setting_path] if isinstance(setting_path, (str, Path)) else setting_path
    md_apps: List[str] = [setting_app] if isinstance(setting_app, str) else setting_app
    
    # Normalize base_templates to a list
    if setting_base_template is None:
        # Use built-in sidebar template as default for better out-of-box experience
        default_template = 'django_spellbook/bases/sidebar_left.html'
        if md_apps:
            base_templates = [default_template] * len(md_apps)
        else:
            base_templates = [default_template]
    elif isinstance(setting_base_template, str):
        # If a string, use the same template for all sources
        base_templates = [setting_base_template] * len(md_apps)
    else:
        # Assume it's already a list
        base_templates = setting_base_template
        
    return md_paths, md_apps, base_templates

def validate_spellbook_settings():
    """
    Validate required settings and support multiple source-destination pairs.

    Returns:
        Tuple[List[str], List[str], List[str], List[Optional[str]], List[Optional[str]]]:
        md_paths, md_apps, md_url_prefix, base_templates, extend_from_templates.
    """
    # Get settings values with backward compatibility
    md_path = getattr(settings, 'SPELLBOOK_MD_PATH', None)
    md_app = getattr(settings, 'SPELLBOOK_MD_APP', None)
    md_url_prefix = getattr(settings, 'SPELLBOOK_MD_URL_PREFIX', None)
    md_base_template = getattr(settings, 'SPELLBOOK_MD_BASE_TEMPLATE', None)
    md_extend_from = getattr(settings, 'SPELLBOOK_BASE_EXTEND_FROM', None)

    # Normalize settings to lists
    md_file_paths, content_apps, base_templates = normalize_settings(md_path, md_app, md_base_template)

    # Normalize URL prefixes
    md_url_prefixes = normalize_url_prefixes(md_url_prefix)

    if not content_apps:
        raise CommandError("Missing required settings: SPELLBOOK_MD_APP or SPELLBOOK_CONTENT_APP")

    # Normalize extend_from to list (after content_apps validation)
    if md_extend_from is None:
        extend_from_templates = [None] * len(content_apps)
    elif isinstance(md_extend_from, str):
        extend_from_templates = [md_extend_from] * len(content_apps)
    else:
        extend_from_templates = md_extend_from

    # Generate default URL prefixes if not provided
    if not md_url_prefixes:
        # Generate default prefixes based on app names
        if len(content_apps) == 1:
            md_url_prefixes = ['']  # Single app gets empty prefix
        else:
            # First app gets empty prefix, others use their app name as prefix
            md_url_prefixes = [''] + content_apps[1:]

    # Validate settings
    _validate_setting_values(md_file_paths, content_apps, md_url_prefixes, base_templates)
    _validate_base_templates(base_templates)
    _validate_extend_from_setting(extend_from_templates, content_apps)

    return md_file_paths, content_apps, md_url_prefixes, base_templates, extend_from_templates

def _validate_setting_values(md_file_paths: List[str], content_apps: List[str], md_url_prefix: List[str], base_templates: List[Optional[str]]):
    """
    Validate setting values for correctness and compatibility.
    
    Args:
        md_file_paths (List[str]): List of paths to markdown files.
        content_apps (List[str]): List of content app names.
        md_url_prefix (List[str]): List of URL prefixes for the content app.
        base_templates (List[Optional[str]]): List of base templates.
        
    Raises:
        CommandError: If any settings are missing or invalid.
    """
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
    if len(md_url_prefix) != len(content_apps):
        raise CommandError("SPELLBOOK_MD_URL_PREFIX and SPELLBOOK_MD_APP must have the same number of entries")
    if len(base_templates) != len(content_apps):
        raise CommandError("SPELLBOOK_MD_BASE_TEMPLATE and SPELLBOOK_MD_APP must have the same number of entries")
    
    # Ensure each string is not empty
    for md_path in md_file_paths:
        if not md_path:
            raise CommandError(
                "Invalid SPELLBOOK_MD_PATH configuration!\n"
                "Reason: Empty value found in path list\n"
                "Solution: Ensure all paths in settings.SPELLBOOK_MD_PATH "
                "are non-empty strings\n"
                "Documentation: https://django-spellbook.org/docs/settings/"
            )
    for app_setting in content_apps:
        if not app_setting:
            raise CommandError("SPELLBOOK_MD_APP must be a non-empty string.")

    # Validate apps are in INSTALLED_APPS (skip in test environment)
    # Check if each app exists in INSTALLED_APPS (including AppConfig format like 'app.apps.AppConfig')
    # Skip validation if TESTING flag is set (used in tests to avoid module import errors)
    if not getattr(settings, 'TESTING', False):
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        missing_apps = []

        for app in content_apps:
            # Check if app is directly in INSTALLED_APPS or as part of an AppConfig path
            app_found = False
            for installed_app in installed_apps:
                # Match exact app name or app config pattern like 'app.apps.AppConfig'
                if installed_app == app or installed_app.startswith(f'{app}.'):
                    app_found = True
                    break

            if not app_found:
                missing_apps.append(app)

        if missing_apps:
            missing_apps_list = '\n  - '.join(missing_apps)
            raise CommandError(
                f"The following apps in SPELLBOOK_MD_APP are not in INSTALLED_APPS:\n"
                f"  - {missing_apps_list}\n\n"
                f"Please add these apps to INSTALLED_APPS in your settings.py:\n\n"
                f"INSTALLED_APPS = [\n"
                f"    ...\n"
                f"    {', '.join(repr(app) for app in missing_apps)},\n"
                f"]"
            )

    # Validate URL prefixes
    for prefix in md_url_prefix:
        # Check for dangerous patterns
        dangerous_patterns = ['..', '//', '<?', '%', '\x00']
        if any(pattern in prefix for pattern in dangerous_patterns):
            raise CommandError(f"URL prefix '{prefix}' contains invalid characters.")

        # Check for invalid URL characters
        import re
        if prefix and not re.match(r'^[a-zA-Z0-9_\-]+$', prefix):
            logger.warning(f"URL prefix '{prefix}' contains characters that may cause issues with URL routing.")

def _validate_extend_from_setting(extend_from: List[Optional[str]], content_apps: List[str]):
    """
    Validate SPELLBOOK_BASE_EXTEND_FROM setting.

    Args:
        extend_from: List of template paths to extend from
        content_apps: List of content app names

    Raises:
        CommandError: If invalid values detected
    """
    # Check list length matches
    if len(extend_from) != len(content_apps):
        raise CommandError(
            f"SPELLBOOK_BASE_EXTEND_FROM has {len(extend_from)} entries "
            f"but SPELLBOOK_MD_APP has {len(content_apps)}. "
            f"Use None for apps using standalone Spellbook."
        )

    # Validate each non-None template
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist

    for i, template_path in enumerate(extend_from):
        if template_path is None:
            continue

        # Check template exists
        try:
            template = get_template(template_path)
        except TemplateDoesNotExist:
            raise CommandError(
                f"SPELLBOOK_BASE_EXTEND_FROM template not found: '{template_path}'"
            )

        # Check for required block
        template_source = template.template.source
        if '{%' in template_source and 'block spellbook' not in template_source:
            raise CommandError(
                f"Template '{template_path}' missing required block: 'spellbook'\n\n"
                f"Add this to your template:\n"
                f"    {{% block spellbook %}}{{% endblock %}}"
            )

def _validate_base_templates(base_templates: List[Optional[str]]):
    """Validate base template values."""
    for template in base_templates:
        if template is not None:
            if not isinstance(template, str):
                raise CommandError(f"Base template '{template}' must be None or a string.")
            
            # Check for dangerous template path patterns
            dangerous_patterns = [
                '..', '//', '\\', '<', '>', '%', '\x00', 
                ':', '&', ';', '$', '|', '?', '#', '*', '(', ')',
                '`touch ', '`rm -rf /`'
                ]
            if any(pattern in template for pattern in dangerous_patterns):
                raise CommandError(
                    f"Base template path '{template}' contains potentially dangerous characters.\n"
                    "Avoid path traversal sequences and special characters in template paths."
                )
            
            # Verify the template path doesn't try to escape the template directory
            normalized_path = os.path.normpath(template)
            if normalized_path.startswith('..') or normalized_path.startswith('/'):
                raise CommandError(
                    f"Base template path '{template}' contains potentially dangerous characters.\n"
                    "Template paths should be relative to the template directory without traversal."
                )
def setup_directory_structure(content_app: str, dirpath: str):
    """
    Set up the necessary directory structure for content processing.
    
    Args:
        content_app (str): Name of the content app.
        dirpath (str): Path to the directory containing the markdown files.
    
    Returns:
        Tuple[str, str]: content_dir_path and template_dir.
    
    Raises:
        CommandError: If the content app is not found in the directory.
    """
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

def setup_template_directory(content_dir_path: str, content_app: str):
    """
    Set up the template directory structure.
    
    Args:
        content_dir_path (str): Path to the content app directory.
        content_app (str): Name of the content app.
    
    Returns:
        str: Path to the template directory.
    
    Raises:
        CommandError: If the template directory could not be created.
    """
    try:
        base_template_dir = Path(content_dir_path) / 'templates' / content_app / 'spellbook_md'
        base_template_dir.mkdir(parents=True, exist_ok=True)
        return str(base_template_dir)
    except Exception as e:
        raise CommandError(f"Could not create template directory: {str(e)}")

def get_folder_list(dirpath: str, md_file_path: str):
    """
    Get list of folders from dirpath relative to md_file_path.
    
    Args:
        dirpath (str): Path to the directory containing the markdown files.
        md_file_path (str): Path to the markdown file.
    
    Returns:
        List[str]: List of folders.
    """
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

def log_and_write(message: str, level: str = 'info', stdout: Optional[IO] = None) -> None:
    """
    Log a message and optionally write to stdout.
    
    Args:
        message: The message to log and write
        level: The logging level (debug, info, warning, error)
        stdout: Optional output stream to write to
    """
    getattr(logger, level)(message)
    if stdout:
        stdout.write(message)
        
        
def normalize_url_prefix(prefix: str) -> str:
    """
    Normalize URL prefix by removing leading/trailing slashes.
    
    Args:
        prefix (str): URL prefix to normalize
        
    Returns:
        str: Normalized URL prefix
    """
    # Remove leading and trailing slashes
    prefix = prefix.strip('/')
    return prefix

def normalize_url_prefixes(setting_url_prefix) -> List[str]:
    """
    Normalize URL prefixes to a list.

    Args:
        setting_url_prefix: URL prefix or list of prefixes

    Returns:
        List[str]: Normalized list of URL prefixes
    """
    if setting_url_prefix is None:
        return []
    elif isinstance(setting_url_prefix, str):
        return [normalize_url_prefix(setting_url_prefix)]
    else:
        return [normalize_url_prefix(p) for p in setting_url_prefix]


