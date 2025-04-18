from django.core.management.base import CommandError

# Custom Exception Classes
class SpellbookMDError(CommandError):
    """Base exception for all Spellbook MD errors."""
    pass

class ConfigurationError(SpellbookMDError):
    """Error related to configuration issues (settings, paths, etc.)."""
    pass

class ContentDiscoveryError(SpellbookMDError):
    """Error related to finding and parsing content files."""
    pass

class ProcessingError(SpellbookMDError):
    """Error during markdown processing."""
    pass

class OutputGenerationError(SpellbookMDError):
    """Error generating templates, views, or URLs."""
    pass