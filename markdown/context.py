# django_spellbook/markdown/context.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SpellbookContext:
    # Required fields
    title: str
    created_at: datetime
    updated_at: datetime
    url_path: str
    raw_content: str

    # Optional fields
    is_public: bool = True
    tags: List[str] = field(default_factory=list)
    custom_meta: Dict[str, any] = field(default_factory=dict)
    toc: Dict[str, Dict] = field(default_factory=dict)
    next_page: Optional[str] = None
    prev_page: Optional[str] = None
