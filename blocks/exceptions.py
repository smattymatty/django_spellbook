class SpellBlockError(Exception):
    """Base exception for spell block errors"""
    pass


class BlockRegistrationError(SpellBlockError):
    """Raised when there's an error registering a block"""
    pass


class BlockTemplateError(SpellBlockError):
    """Raised when there's an error with a block's template"""
    pass


class BlockRenderError(SpellBlockError):
    """Raised when there's an error rendering a block"""
    pass


class BlockConfigurationError(SpellBlockError):
    """Raised when a block is incorrectly configured"""
    pass
