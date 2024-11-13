from typing import Set

from .base import BasicSpellBlock
from .registry import SpellBlockRegistry

# Export what we want available at the package level
__all__ = ['BasicSpellBlock', 'SpellBlockRegistry']


def create_block(name: str, template: str,
                 required_kwargs: Set[str] = None,
                 optional_kwargs: Set[str] = None):
    """Create and register a new block"""
    block = BasicSpellBlock(name, template, required_kwargs, optional_kwargs)
    SpellBlockRegistry.register(name)(block)
    return block
