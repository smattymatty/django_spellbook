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

from django_spellbook.management.commands.spellbook_md_p.reporter import MarkdownReporter

logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class SpellblockStatistics:
    """Statistics for a single spellblock."""
    name: str
    # TODO: Add more stats like template, context, per-file usage, etc.
    total_uses: int
    failed_uses: int
    
    


@lru_cache(maxsize=1)
def discover_blocks(reporter: MarkdownReporter) -> int:
    """
    Discover and register spell blocks from all installed apps.
    
    This function attempts to import a 'spellblocks' module from each installed
    Django app and register any spell blocks defined there.
    
    Args:
        reporter: MarkdownReporter object for logging
        
    Raises:
        CommandError: If a critical error occurs during block discovery
    
    Returns:
        Number of blocks discovered and registered
    """
    reporter.write("Discovering blocks...", level='minimal')
    
    # First discover blocks from all apps
    for app_config in apps.get_app_configs():
        try:
            # Try to import spellblocks.py from each app
            module_path = f"{app_config.name}.spellblocks"
            reporter.write(f"Checking {module_path}...", level='debug')

            importlib.import_module(module_path)
            reporter.write(f"Discovered blocks from {app_config.name}", level='detailed')
            
        except ImportError:
            # Skip if no spellblocks.py exists
            reporter.write(f"No spellblocks.py found in {app_config.name}", level='debug')
            continue
        except Exception as e:
            reporter.write(f"Error loading blocks from {app_config.name}: {str(e)}", level='debug')
            continue

    # Now, get all registered blocks from the registry
    block_count = len(SpellBlockRegistry._registry)
    
    # Create statistics objects for each registered block
    for block_name in SpellBlockRegistry._registry:
        reporter.spellblocks.append(build_new_spellblock_statistics(block_name))
    
    reporter.write(f"Block discovery complete. Found {block_count} blocks.", level='detailed')
    
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

def build_new_spellblock_statistics(name: str) -> SpellblockStatistics:
        """
        Build a new SpellblockStatistics object for a given spellblock name.
        
        Args:
            name: Name of the spellblock
        
        Returns:
            SpellblockStatistics object
        """
        return SpellblockStatistics(name, 0, 0)
