# django_spellbook/markdown/toc.py
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


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

        # Handle root-level files
        if not parts:
            current.children[file_path.stem] = TOCEntry(
                title=title,
                url=url,
            )
            return

        # Handle nested files
        for part in parts:
            if part not in current.children:
                current.children[part] = TOCEntry(
                    title=part.replace('-', ' ').title(),
                    url=part,  # Just use the directory name
                )
            current = current.children[part]

        # Add the actual file
        filename = file_path.stem
        current.children[filename] = TOCEntry(
            title=title,
            url=url,  # Use the full provided URL for files
        )

    def get_toc(self) -> Dict:
        """Get the complete TOC structure"""
        def _convert_to_dict(entry: TOCEntry) -> Dict:
            result = {
                'title': entry.title,
                'url': entry.url,
            }
            if entry.children:
                result['children'] = {
                    k: _convert_to_dict(v)
                    for k, v in sorted(entry.children.items())
                }
            return result

        return _convert_to_dict(self.root)
