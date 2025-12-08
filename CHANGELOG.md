# Changelog

All notable changes to Django Spellbook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-08

### ⚠️ Breaking Changes
- **Removed Django-like tag syntax** (`{% div %}`, `{% enddiv %}`)
- All HTML elements must now use SpellBlock syntax (`{~ div ~}`, `{~~}`)
- Removed 3 internal markdown extension files (~484 lines)
- Removed 77 deprecated tests

### Added
- **10 HTML Element SpellBlocks**: `div`, `section`, `article`, `aside`, `header`, `footer`, `nav`, `main`, `hr`, `br`
- **CSS-style shorthand syntax**: `.classname` and `#id-name` within SpellBlock tags
- **Hyphenated attribute support**: Full support for `hx-*`, `data-*`, `aria-*`, `@click`, `:bind`, and other special characters
- **HTMX integration**: Seamless support for all HTMX attributes
- **Alpine.js integration**: Native support for Alpine.js directives (`@click`, `x-data`, `x-show`, etc.)
- **Vue.js integration**: Support for Vue.js binding syntax (`:bind`, `@event`)
- **Generic HTMLElementBlock base class** for creating custom HTML element blocks
- **Comprehensive attribute parser** with quote preservation and intelligent shorthand merging

### Changed
- Enhanced attribute parser to support CSS-style shorthand (`.class`, `#id`)
- Improved regex to handle special characters in attribute names (`@`, `:`, `-`)
- Markdown extensions reduced from 8 to 7 (removed DjangoLikeTagExtension)
- Cleaner codebase: removed 864 lines of deprecated code

### Migration from 0.1.x

**Regex pattern for bulk migration:**
```
Find:    {% (\w+) ([^%]*) %}(.*?){% end\1 %}
Replace: {~ $1 $2 ~}$3{~~}
```

**Manual migration examples:**
| Old Syntax (0.1.x) | New Syntax (0.2.0) |
|--------------------|---------------------|
| `{% div .my-class %}` | `{~ div .my-class ~}` |
| `{% div #my-id %}` | `{~ div #my-id ~}` |
| `{% section %}` | `{~ section ~}` |
| `{% enddiv %}` | `{~~}` |
| `{% endsection %}` | `{~~}` |

**What still works:**
- All existing SpellBlocks (`alert`, `card`, `hero`, `button`, `accordion`, `practice`, `quote`, etc.)
- SpellBlock syntax `{~ blockname ~}content{~~}`
- All theme system features
- All markdown processing features
- Automatic sitemap generation
- Prev/next navigation

**Why this change:**
- More consistent syntax across the entire library
- Better support for modern frameworks (HTMX, Alpine.js, Vue.js)
- Cleaner separation from actual Django template tags
- Improved attribute parsing with CSS-style shorthand
- Simplified codebase and better maintainability

---

## [0.1.18] - 2025-12-08

### Added

#### Automatic Sitemap.xml Generation
Django Spellbook now automatically generates SEO-friendly sitemaps from your markdown content - zero configuration required!

**What you get:**
- **Automatic sitemap generation** - Runs during `python manage.py spellbook_md`
- **Smart filtering** - Respects `is_public: false` frontmatter
- **Date handling** - Uses `modified` date (falls back to `published`) for `<lastmod>`
- **URL prefix support** - Works with multi-source configurations
- **Per-page control** - Optional frontmatter overrides for priority and changefreq

**Quick setup:**
```python
# settings.py
SPELLBOOK_SITE_URL = "https://your-site.com"  # Required for sitemap generation
```

**Advanced configuration (optional):**
```python
# settings.py
SPELLBOOK_SITEMAP_ENABLED = True  # Default: True if SITE_URL is set
SPELLBOOK_SITEMAP_OUTPUT = "static/sitemap.xml"  # Default: "sitemap.xml"
```

**Per-page frontmatter options:**
```yaml
---
title: Important Page
sitemap_priority: 0.9      # 0.0-1.0 (default: omitted)
sitemap_changefreq: daily  # always, hourly, daily, weekly, monthly, yearly, never
sitemap_exclude: true      # Exclude from sitemap but keep page public
---
```

**How it works:**
- Automatically generates sitemap.xml after processing all markdown files
- Filters out pages with `is_public: false`
- Respects per-page `sitemap_exclude` flag
- Uses `modified` or `published` dates for `<lastmod>` tag
- Supports multi-source configurations (all apps in one sitemap)
- Gracefully skips if `SPELLBOOK_SITE_URL` not configured

**XML Output:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://your-site.com/docs/intro/</loc>
    <lastmod>2025-12-08</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

**Benefits:**
- ✅ Improves SEO - Search engines discover all your content
- ✅ Zero maintenance - Updates automatically on every build
- ✅ Smart defaults - Works great with no configuration
- ✅ Full control - Per-page overrides when you need them

#### Automatic Prev/Next Page Navigation
Your documentation and blog posts now have **automatic sequential navigation** - zero configuration required!

**What you get:**
- **Filesystem-based navigation** - Files automatically link in alphabetical order within directories
- **Directory boundaries** - Navigation respects folder structure (won't jump between different sections)
- **Frontmatter overrides** - Manually specify prev/next in YAML when needed
- **Beautiful UI** - Theme-aware navigation buttons with hover effects

**Example (automatic):**
```
docs/
  01-intro.md     → next: 02-setup
  02-setup.md     → prev: 01-intro, next: 03-usage
  03-usage.md     → prev: 02-setup
```

**Example (custom frontmatter):**
```yaml
---
title: Advanced Configuration
prev: introduction              # Path format
next: docs:troubleshooting     # Namespaced format
---
```

**How it works:**
- Runs during `python manage.py spellbook_md`
- Navigation links added to metadata display automatically
- Supports both path-based (`intro`) and namespaced (`blog:intro`) formats
- 25 comprehensive tests ensuring reliability

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

This was caused by the `sane_lists` extension requiring blank lines before lists. Removed `sane_lists` to allow more flexible list rendering that matches modern markdown behavior.

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