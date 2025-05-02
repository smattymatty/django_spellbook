# django_spellbook/markdown/context.py
from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any

from .content_metrics import get_word_count, get_reading_time_minutes

logger = logging.getLogger(__name__)

@dataclass
class SpellbookContext:
    # Required fields
    title: str
    url_path: str
    raw_content: str

    # Optional fields
    published: Optional[datetime] = None
    modified: Optional[datetime] = None
    is_public: bool = True
    tags: List[str] = field(default_factory=list)
    custom_meta: Dict[str, any] = field(default_factory=dict)
    toc: Dict[str, Dict] = field(default_factory=dict)
    next_page: Optional[str] = None
    prev_page: Optional[str] = None
    
    # Content Metrics (calculated dynamically)
    word_count: int = 0
    reading_time_minutes: int = 0

    
    def get_safe_attr(self, attr_name: str, default: Any = None) -> Any:
        """Safely get attribute with a default fallback."""
        return getattr(self, attr_name, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary, handling special cases."""
        try:
            result = {}
            for k, v in self.__dict__.items():
                if k == 'toc':  # Skip toc as it's handled separately
                    continue
                try:
                    # convert datetime objects to their representation
                    if isinstance(v, datetime):
                        result[k] = repr(v)
                    # this is to test error handling
                    elif v == "Arbitrary Error String, Very Specific for Testing Purposes":
                        raise ValueError("Arbitrary Error String")
                    # default case
                    else:
                        result[k] = v
                except Exception as e:
                    logger.warning(f"Could not process context value for key '{k}': {str(e)}")
                    raise ValueError(f"Error processing context value for key '{k}': {str(e)}") from e
            return result
        except Exception as e:
            logger.error(f"Error converting context to dictionary: {str(e)}")
            raise RuntimeError(f"Critical error converting context to dictionary: {str(e)}") from e

    def prepare_metadata(self, content_app: str, relative_url: str) -> Dict[str, Any]:
        """Prepare metadata dictionary with content app and URL info."""
        from django_spellbook.management.commands.processing.generator_utils import get_clean_url
        self._ensure_metadata_required_fields()
        path_parts = relative_url.split('/')
        url_name = relative_url.replace('/', '_')
        
        metadata = {
            'title': self.get_safe_attr('title', path_parts[-1].replace('-', ' ').title()),
            'published': self.get_safe_attr('published', None),
            'modified': self.get_safe_attr('modified', None),
            'url_path': get_clean_url(relative_url),
            'raw_content': self.get_safe_attr('raw_content', ''),
            'is_public': self.get_safe_attr('is_public', True),
            'tags': self.get_safe_attr('tags', []),
            'custom_meta': self.get_safe_attr('custom_meta', {}),
            'namespace': content_app,
            'url_name': url_name,
            'namespaced_url': f"{content_app}:{url_name}",
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes
        }
        
        return metadata
    
    def _ensure_metadata_required_fields(self):
        '''Ensure required metadata fields are set.'''
        if self.raw_content:
            # word_count and reading_time_minutes are calculated dynamically
            self.calculate_metrics()
        else:
            raise ValueError("Raw content is empty")


    def validate(self) -> List[str]:
        """Validate required context attributes."""
        errors = []
        required_fields = ['title', 'url_path', 'raw_content']
        for field in required_fields:
            if not hasattr(self, field) or getattr(self, field) is None:
                errors.append(f"Missing required field: {field}")
        return errors
    
    def calculate_metrics(self):
        """Calculate content metrics"""
        self.word_count = get_word_count(self.raw_content)
        self.reading_time_minutes = get_reading_time_minutes(self.raw_content)
        
        
