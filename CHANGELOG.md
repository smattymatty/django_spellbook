# Changelog

All notable changes to Django Spellbook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.17] - TBD

### Fixed

#### Table of Contents External Link Navigation
- **Fixed TOC not expanding from external links** - Visiting a page from outside the site (bookmarks, search engines, direct links) now properly highlights and expands the TOC to show your current location
- **Fixed URL matching** - View generator now uses Django namespaced URLs (`docs:Commands_spellbook_md`) instead of path-style URLs (`Commands/spellbook_md`) to match the TOC structure
- **Fixed parent/child URL duplication** - Parent directories no longer share URLs with their child pages, eliminating confusion about which item should be active
- **Removed jarring page load animation** - TOC now expands instantly on page load (no visible transition), but user interactions still animate smoothly
- **Modern JavaScript architecture** - Extracted 200+ lines of inline JavaScript into a clean ES module (`toc.mjs`) for better maintainability

### Changed

#### Test Infrastructure
- **Added TESTING flag** - Tests now use `TESTING=True` in `tests/settings.py` to skip INSTALLED_APPS validation, preventing 100+ spurious test failures
- **Fixed test decorators** - Added `TESTING=True` to `@override_settings` decorators across test suite
- **All 674 tests passing** - Went from 102 failures → 0 failures with the new testing approach

### Technical Details
- `view_generator.py` - Views now pass namespaced URLs in context
- `toc.py` - Parent directories have empty URLs; only leaf pages have URLs
- `toc.mjs` - New ES module with smart expansion logic and no-transition on initial load
- `sidebar_toc.html` - Added `toc-no-transition` class to prevent jarring animations
- Test files updated to use TESTING flag for clean test runs

## [0.1.16] - 2025-08-21

### Added

#### Theme System
- **Python-based color configuration** - Define your entire site's color scheme in Django settings instead of CSS files
- **9 magical theme presets** ready to use:
  - `default` - Classic blue spellbook theme
  - `arcane` - Deep purple mysteries with golden spell glows
  - `celestial` - Divine light magic with sky blues and gold
  - `forest` - Woodland greens and earth tones
  - `ocean` - Deep sea blues and aquatic enchantments
  - `phoenix` - Fire colors with oranges and reds
  - `shadow` - Monochrome shadow magic
  - `enchanted` - Bright magical pinks and fairy gold
  - `pastel` - Soft, gentle enchantment colors

- **Custom color support** - Define your own magical color palette:
  ```python
  SPELLBOOK_THEME = {
      'colors': {
          'primary': '#8B008B',
          'secondary': '#4B0082',
          'accent': '#FFD700',
      }
  }
  ```

- **Automatic opacity variants** - Every color automatically gets 25%, 50%, and 75% transparent versions using CSS color-mix
- **Custom color names** - Create your own spell colors like `magic`, `spell`, `potion` that work with all utility classes
- **Dynamic theme switching** - Change themes at runtime using sessions and middleware
- **100% backward compatible** - Existing sites continue working without any changes

### Technical Details
- New `django_spellbook.theme` module with validation, generation, and preset management
- CSS variables dynamically generated from Python configuration
- Comprehensive color validation supporting hex, rgb, rgba, and CSS named colors
- Full test coverage with 26 new tests for the theme system
- Template tag `{% spellbook_styles %}` enhanced to inject theme CSS while maintaining backward compatibility

### Usage
```python
# settings.py
from django_spellbook.theme import THEMES

# Use a preset theme
SPELLBOOK_THEME = THEMES['arcane']

# Or create your own
SPELLBOOK_THEME = {
    'colors': {
        'primary': '#FF6B35',
        'secondary': '#F77B71',
        # ... your colors
    },
    'custom_colors': {
        'magic': '#8B008B',  # Use as sb-bg-magic
        'spell': '#4B0082',  # Use as sb-text-spell
    }
}
```

### Developer Notes
- Theme CSS is generated once per request (caching can be added if needed)
- No JavaScript required - pure CSS variable approach
- No build step or compilation needed
- Compatible with all existing SpellBlocks and utility classes