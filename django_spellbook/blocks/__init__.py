from typing import Set

# render to string
from django.template.loader import render_to_string

from .base import BasicSpellBlock
from .registry import SpellBlockRegistry


# Export what we want available at the package level
__all__ = ['BasicSpellBlock', 'SpellBlockRegistry']
