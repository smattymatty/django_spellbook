[![PyPI Downloads](https://static.pepy.tech/personalized-badge/django-spellbook?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/django-spellbook)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django_spellbook/)

# Django Spellbook

A markdown engine for Django with reusable components, theming, and automatic site generation. One function for dynamic content. One command for static sites.

[Documentation](https://django-spellbook.org/) · [Quick Start](https://django-spellbook.org/docs/quick-start/) · [SpellBlocks Showcase](https://django-spellbook.org/examples/introduction/)

## The Function
```python
from django_spellbook.parsers import spellbook_render

html = spellbook_render("""
# Welcome

{~ alert type="success" ~}
Your account is ready.
{~~}
""")
```

Markdown in, HTML out, with full component support. Use it in views, APIs, emails, admin panels—anywhere.

## The Command
```bash
python manage.py spellbook_md
```

Point Spellbook at a folder of markdown files. Get a complete Django content system:

- Templates with rendered content
- View functions for each page
- URL patterns matching your folder structure
- Sidebar navigation with table of contents
- Previous/next page links
- Automatic sitemap.xml
```python
# settings.py — minimal config
SPELLBOOK_MD_PATH = BASE_DIR / 'content'
SPELLBOOK_MD_APP = 'my_app'
```

Your folder hierarchy becomes your URL hierarchy. Frontmatter becomes page metadata. Done.

## SpellBlocks

Reusable content components embedded directly in markdown.
```markdown
{~ alert type="warning" ~}
This requires Django 5.0 or higher.
{~~}

{~ card title="Quick Install" ~}
`pip install django-spellbook`
{~~}

{~ accordion title="More Details" ~}
Hidden until clicked.
{~~}
```

Built-in: `alert`, `card`, `accordion`, `quote`, `hero`, `progress`, `practice`, `button`.

**Create your own:**
```python
from django_spellbook.blocks import BasicSpellBlock
from django_spellbook.registry import SpellBlockRegistry

@SpellBlockRegistry.register()
class MyBlock(BasicSpellBlock):
    name = 'myblock'
    template = 'blocks/myblock.html'

    def get_context(self):
        context = super().get_context()
        context['variant'] = self.kwargs.get('variant', 'default')
        return context
```

Now `{~ myblock variant="fancy" ~}` works everywhere.

## HTML Elements

Raw HTML structure with full attribute support.
```markdown
{~ div .container #main data-section="intro" ~}
Classes, IDs, data attributes.
{~~}
```

HTMX and Alpine.js work here:
```markdown
{~ button hx-get="/api/users" hx-target="#results" ~}
Load Users
{~~}

{~ div x-data="{ open: false }" ~}
  {~ button @click="open = !open" ~}Toggle{~~}
  {~ div x-show="open" ~}Revealed!{~~}
{~~}
```

Available: `div`, `section`, `article`, `aside`, `header`, `footer`, `nav`, `main`, `p`, `span`, `hr`, `br`.

## Themes

One line changes your entire color scheme:
```python
from django_spellbook.theme import THEMES

SPELLBOOK_THEME = THEMES['arcane']      # Deep purple
# SPELLBOOK_THEME = THEMES['forest']    # Woodland greens
# SPELLBOOK_THEME = THEMES['ocean']     # Deep sea blues
# SPELLBOOK_THEME = THEMES['phoenix']   # Fire colors
# SPELLBOOK_THEME = THEMES['celestial'] # Divine blues and gold
```

Or define your own:
```python
SPELLBOOK_THEME = {
    'colors': {
        'primary': '#8B008B',
        'secondary': '#4B0082',
        'accent': '#FFD700',
    }
}
```

One template tag loads everything—components, utilities, theme colors:
```html
{% load spellbook_tags %}
{% spellbook_styles %}
```

## Advanced Configuration
```python
# Multiple source directories
SPELLBOOK_MD_PATH = [BASE_DIR / 'docs', BASE_DIR / 'blog']
SPELLBOOK_MD_APP = ['docs_app', 'blog_app']
SPELLBOOK_MD_URL_PREFIX = ['docs', 'blog']

# Custom base template (or None for raw HTML)
SPELLBOOK_MD_BASE_TEMPLATE = 'my_app/custom_base.html'
```

## Install
```bash
pip install django-spellbook
```
```python
INSTALLED_APPS = [
    'django_spellbook',
]
```

## Docs

- [Quick Start](https://django-spellbook.org/docs/quick-start/)
- [spellbook_render()](https://django-spellbook.org/docs/spellbook-render/)
- [SpellBlocks Reference](https://django-spellbook.org/examples/introduction/)
- [Custom SpellBlocks](https://django-spellbook.org/docs/custom-spellblocks/)
- [Themes](https://django-spellbook.org/docs/themes/)
- [Configuration](https://django-spellbook.org/docs/configuration/)