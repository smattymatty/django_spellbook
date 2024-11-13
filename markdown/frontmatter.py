# django_spellbook/markdown/frontmatter.py
import yaml
from datetime import datetime
from pathlib import Path
from .context import SpellbookContext


class FrontMatterParser:
    def __init__(self, content: str, file_path: Path):
        self.content = content
        self.file_path = file_path
        self.raw_content = ""
        self.metadata = {}
        self._parse()

    def _parse(self):
        """Parse front matter and content"""
        if self.content.startswith('---'):
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                try:
                    # Use safe_load with explicit encoding handling
                    yaml_content = parts[1].encode('utf-8').decode('utf-8')
                    self.metadata = yaml.safe_load(yaml_content) or {}
                    if not isinstance(self.metadata, dict):
                        self.metadata = {}
                    self.raw_content = parts[2].strip()
                except (yaml.YAMLError, AttributeError, UnicodeError):
                    self.metadata = {}
                    self.raw_content = self.content
            else:
                self.metadata = {}
                self.raw_content = self.content
        else:
            self.metadata = {}
            self.raw_content = self.content

    def get_context(self, url_path: str) -> SpellbookContext:
        stats = self.file_path.stat()
        return SpellbookContext(
            title=self.metadata.get('title', self.file_path.stem),
            created_at=datetime.fromtimestamp(stats.st_ctime),
            updated_at=datetime.fromtimestamp(stats.st_mtime),
            url_path=url_path,
            raw_content=self.raw_content,
            is_public=multi_bool(self.metadata.get('is_public', True)),
            tags=self.metadata.get('tags', []),
            custom_meta={k: v for k, v in self.metadata.items()
                         if k not in ['title', 'is_public', 'tags']},  # Fixed 'public' to 'is_public'
            toc={},  # This will be filled by the command
            next_page=None,
            prev_page=None
        )


def multi_bool(value):
    """Allow string false or False or boolean False to be False
    or string true or True or boolean True to be True"""
    if isinstance(value, str):
        if value.lower() in ['false', 'f', 'no', 'n', '0']:
            return False
        elif value.lower() in ['true', 't', 'yes', 'y', '1']:
            return True
    return bool(value)
