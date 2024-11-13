from typing import Dict, Type, Optional
import importlib
import logging

from django.apps import apps

from .base import BasicSpellBlock
from .exceptions import BlockRegistrationError


logger = logging.getLogger(__name__)


class SpellBlockRegistry:
    """Registry for spell blocks"""
    _registry: Dict[str, Type[BasicSpellBlock]] = {}
    _discovery_in_progress = False  # Add this flag

    @classmethod
    def register(cls, name: Optional[str] = None):
        """Decorator to register a spell block"""
        def decorator(block_class: Type[BasicSpellBlock]):
            try:
                # Validate the block class
                if not issubclass(block_class, BasicSpellBlock):
                    raise BlockRegistrationError(
                        f"Block class {block_class.__name__} must inherit from BasicSpellBlock"
                    )

                # Get the block name
                block_name = name or getattr(block_class, 'name', None)
                if not block_name:
                    raise BlockRegistrationError(
                        f"Block class {block_class.__name__} must have a name"
                    )

                # Check for name conflicts
                if block_name in cls._registry:
                    raise BlockRegistrationError(
                        f"Multiple blocks registered with name '{block_name}'"
                    )

                # Register the block
                cls._registry[block_name] = block_class
                logger.debug(f"Successfully registered block: {block_name}")
                return block_class

            except Exception as e:
                logger.error(
                    f"Error registering block {block_class.__name__}: {str(e)}")
                raise BlockRegistrationError(str(e))
        return decorator

    @classmethod
    def get_block(cls, name: str) -> Optional[Type[BasicSpellBlock]]:
        """Get a block class by name"""
        return cls._registry.get(name)
