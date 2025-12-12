# django_spellbook/markdown/toc.py
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from django.conf import settings

from django_spellbook.utils import remove_leading_dash, titlefy


@dataclass
class TOCEntry:
    title: str
    url: str
    children: Dict[str, 'TOCEntry'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = {}


class TOCGenerator:
    def __init__(self):
        self.root = TOCEntry(title="root", url="", children={})

    def add_entry(self, file_path: Path, title: str, url: str):
        """Add a file to the TOC structure"""
        parts = file_path.parent.parts
        current = self.root

        title = remove_leading_dash(title)
        title = titlefy(title)
        # split the url by _
        split_url = url.split("_")
        split_url = [remove_leading_dash(part) for part in split_url]
        clean_url = "_".join(split_url)

        # Handle root-level files
        if not parts:
            current.children[file_path.stem] = TOCEntry(
                title=title,
                url=clean_url,
            )
            return

        # Handle nested files
        for part in parts:
            if part not in current.children:
                current.children[part] = TOCEntry(
                    title=part.replace('-', ' ').title(),
                    # Parent directories have no URL (only leaf pages do)
                    url="",
                )
            current = current.children[part]

        # Add the actual file
        filename = file_path.stem
        
        current.children[filename] = TOCEntry(
            title=title,
            # Use the full provided URL for files
            url=clean_url,
        )

    def set_directory_url(self, directory_path: Path, url: str):
        """
        Set the URL for a directory entry in the TOC.

        Args:
            directory_path: Path to the directory (relative to source root)
            url: Django URL name for the directory index view
        """
        if directory_path == Path('.'):
            # Root directory - no action needed
            return

        parts = directory_path.parts
        current = self.root

        # Navigate to the directory entry
        for part in parts:
            if part in current.children:
                current = current.children[part]
            else:
                # Directory not found in TOC (shouldn't happen)
                return

        # Update the URL for this directory
        current.url = url

    def get_toc(self) -> Dict:
        """Get the complete TOC structure"""
        def _convert_to_dict(entry: TOCEntry) -> Dict:
            result = {
                'title': remove_leading_dash(entry.title),
                'url': entry.url,
            }
            if entry.children:
                result['children'] = {
                    k: _convert_to_dict(v)
                    for k, v in sorted(entry.children.items())
                }
            return result

        return _convert_to_dict(self.root)
