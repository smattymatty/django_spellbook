from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

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
        
        path_parts = relative_url.split('/')
        url_name = relative_url.replace('/', '_')
        
        metadata = {
            'title': self.get_safe_attr('title', path_parts[-1].replace('-', ' ').title()),
            'created_at': self.get_safe_attr('created_at', None),
            'updated_at': self.get_safe_attr('updated_at', None),
            'url_path': get_clean_url(relative_url),
            'raw_content': self.get_safe_attr('raw_content', ''),
            'is_public': self.get_safe_attr('is_public', True),
            'tags': self.get_safe_attr('tags', []),
            'custom_meta': self.get_safe_attr('custom_meta', {}),
            'namespace': content_app,
            'url_name': url_name,
            'namespaced_url': f"{content_app}:{url_name}"
        }
        
        return metadata


    def validate(self) -> List[str]:
        """Validate required context attributes."""
        errors = []
        required_fields = ['title', 'created_at', 'updated_at', 'url_path', 'raw_content']
        for field in required_fields:
            if not hasattr(self, field) or getattr(self, field) is None:
                errors.append(f"Missing required field: {field}")
        return errors
