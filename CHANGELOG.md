# Changelog

All notable changes to Django Spellbook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.17] - 2025-12-06

### Changed

#### Beautiful Documentation Out of the Box
Running `python manage.py spellbook_md` now gives you a gorgeous, professional documentation site **automatically** - no configuration needed!

**What you get instantly:**
- **Sidebar table of contents** that's always visible
- **Full theme support** - all 9 built-in themes work immediately
- **Responsive design** - looks great on mobile and desktop
- **Metadata display** - frontmatter data beautifully presented

**Before:** Raw HTML with no styling
**Now:** Production-ready documentation site

**Want to customize?** You still can! Set `SPELLBOOK_MD_BASE_TEMPLATE` in your settings to use your own template, or set it to `None` if you just want the raw HTML.

### Fixed

#### Markdown Lists Work Without Blank Lines
Fixed the annoying bug where markdown lists needed a blank line before them to render properly. Now lists work like GitHub-Flavored Markdown:

**Before:**
```markdown
Some text here.
- List item 1  ← Would NOT render as a list
```

**After:**
```markdown
Some text here.
- List item 1  ← Now renders correctly as a list!
```

This was caused by the `nl2br` extension converting newlines to `<br/>` tags before list detection. Created a custom `ListAwareNl2BrExtension` that intelligently skips newlines before list markers.

#### Themes Now Work Everywhere
Fixed a bug where **only metadata boxes** changed colors when switching themes. Now **everything** responds to your theme:
- Table of contents text and borders
- Body text and headings
- Code blocks and inline code
- All UI elements

**Before:** Switching themes only changed metadata colors, rest stayed the same
**Now:** Entire page transforms with your chosen theme

#### Long Words No Longer Break Layout
Fixed annoying horizontal scrollbar that appeared when table of contents had long words with underscores (like `really_long_function_name_with_underscores`).

**Before:** Long words caused horizontal scrolling in sidebar
**Now:** Long words wrap gracefully, no scrollbar

#### Table of Contents Highlights Your Location
When you visit a page from a bookmark, search engine, or direct link, the table of contents now **automatically expands and highlights** your current location.

**Before:** TOC stayed collapsed when visiting from external links
**Now:** TOC opens to show exactly where you are

#### Smoother Page Loading
Removed the jarring "expanding" animation when pages first load. TOC now appears instantly in the correct state, while clicks still animate smoothly.

**Before:** Distracting flash of animation on every page load
**Now:** Clean, instant page loads with smooth interactions

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