# django_spellbook/management/commands/spellbook_md/discovery.py

import os
import logging
import importlib
from typing import List, Tuple, Optional
from pathlib import Path

from django.apps import apps
from django.core.management.base import CommandError

from django_spellbook.blocks import SpellBlockRegistry

logger = logging.getLogger(__name__)

def discover_blocks(stdout=None):
    """Discover and register spell blocks from all installed apps."""
    if stdout:
        stdout.write("Starting block discovery...")

    for app_config in apps.get_app_configs():
        try:
            # Try to import spellblocks.py from each app
            module_path = f"{app_config.name}.spellblocks"
            if stdout:
                stdout.write(f"Checking {module_path}...")

            importlib.import_module(module_path)
            if stdout:
                stdout.write(f"Discovered blocks from {app_config.name}")

        except ImportError:
            # Skip if no spellblocks.py exists
            if stdout:
                stdout.write(f"No blocks found in {app_config.name}")
            continue
        except Exception as e:
            if stdout:
                stdout.write(f"Error loading blocks from {app_config.name}: {str(e)}")
            logger.error(f"Error loading blocks from {app_config.name}: {str(e)}")
            continue

    block_count = len(SpellBlockRegistry._registry)
    if stdout:
        stdout.write(f"Block discovery complete. Found {block_count} blocks.")
    
    return block_count

def find_markdown_files(source_path):
    """Find all markdown files in the source path."""
    markdown_files = []
    for dirpath, dirnames, filenames in os.walk(source_path):
        for filename in filenames:
            if filename.endswith('.md'):
                markdown_files.append((dirpath, filename))
    return markdown_files