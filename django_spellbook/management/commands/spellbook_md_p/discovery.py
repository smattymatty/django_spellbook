# django_spellbook/management/commands/spellbook_md_p/discovery.py

import os
import logging
from typing import List, Tuple, Optional, IO, Set
from pathlib import Path
import importlib
from functools import lru_cache

from django.apps import apps
from django.core.management.base import CommandError

from django_spellbook.blocks import SpellBlockRegistry
from django_spellbook.management.commands.command_utils import log_and_write

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def discover_blocks(stdout: Optional[IO] = None) -> int:
    """
    Discover and register spell blocks from all installed apps.
    
    This function attempts to import a 'spellblocks' module from each installed
    Django app and register any spell blocks defined there.
    
    Args:
        stdout: Optional output stream to write progress information
        
    Raises:
        CommandError: If a critical error occurs during block discovery
    
    Returns:
        Number of blocks discovered and registered
    """
    log_and_write("Starting block discovery...", stdout=stdout)
    
    for app_config in apps.get_app_configs():
        try:
            # Try to import spellblocks.py from each app
            module_path = f"{app_config.name}.spellblocks"
            log_and_write(f"Checking {module_path}...", 'debug', stdout)

            importlib.import_module(module_path)
            log_and_write(f"Discovered blocks from {app_config.name}", stdout=stdout)

        except ImportError:
            # Skip if no spellblocks.py exists
            log_and_write(f"No blocks found in {app_config.name}", 'debug', stdout)
            continue
        except Exception as e:
            log_and_write(f"Error loading blocks from {app_config.name}: {str(e)}", 'error', stdout)
            continue

    block_count = len(SpellBlockRegistry._registry)
    log_and_write(f"Block discovery complete. Found {block_count} blocks.", stdout=stdout)
    
    return block_count

def find_markdown_files(source_path: str, 
                        exclude_dirs: Optional[Set[str]] = None) -> List[Tuple[str, str]]:
    """
    Find all markdown files in the source path.
    
    Args:
        source_path: Path to the source directory (string or Path object)
        exclude_dirs: Optional set of directory names to exclude from search
    
    Returns:
        List of tuples containing (directory path, filename) for each markdown file
        
    Raises:
        FileNotFoundError: If the source path doesn't exist
        PermissionError: If there are permission issues accessing the directory
    """
    if exclude_dirs is None:
        exclude_dirs = set()
        
    # Convert to Path object for consistent handling
    path = Path(source_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Source path does not exist: {path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {path}")
        
    markdown_files: List[Tuple[str, str]] = []
    
    try:
        for dirpath, dirnames, filenames in os.walk(str(path)):
            # Modify dirnames in-place to exclude certain directories
        
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            
            for filename in filenames:
                if filename.endswith('.md'):
                    markdown_files.append((dirpath, filename))
    except Exception as e:
        logger.error(f"Error finding markdown files: {str(e)}")
        raise
        
    return markdown_files