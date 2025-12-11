[![PyPI Downloads](https://static.pepy.tech/personalized-badge/django-spellbook?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/django-spellbook)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django_spellbook/)

[Documentation Site](https://django-spellbook.org/)

---

# What is Django Spellbook?

Django Spellbook extends Django's templating and rendering capabilities with a focus on markdown-based content. It transforms markdown files into fully-rendered Django templates with auto-generated views and URLs, eliminating boilerplate code while maintaining Django's flexibility.

Django Spellbook integrates with your project by generating server-side code from markdown content.

# Installation

Install the package with pip:
`pip install django-spellbook`

Then, add `django_spellbook` to your Django app's `INSTALLED_APPS` in `settings.py`:

```python
# settings.py
INSTALLED_APPS = [
    ...,
    'django_spellbook',
    'my_app', # another app is required to use as the SPELLBOOK_MD_APP
]
```

Either batch render with `python manage.py spellbook_md` or run the engine manually with `django_spellbook.parsers import render_spellbook_markdown_to_html` helper fucntion.

# Usage - `python manage.py spellbook_md`

## Markdown Parsing and Rendering

Django Spellbook's markdown processor offers a more flexible and Django-like approach to markdown parsing by extending traditional markdown syntax with Django template-like tags and blocks of reusable content components.

### Why Use Spellbook's Markdown Parser?

This parser goes beyond the standard markdown syntax by enabling you to include Django-inspired tags directly in your markdown files. This allows for more structured and semantic HTML, especially useful for projects that need finer control over styling and element attributes, like setting classes or IDs directly in markdown. This means you can write markdown that integrates more seamlessly with your Django templates.

### HTML Element SpellBlocks

Django Spellbook provides HTML element blocks with CSS-style shorthand syntax:

```markdown
{~ div .my-class #my-id ~}
This is a custom div block with a class and an ID.
{~~}
```

The above will render as HTML with the specified class and ID attributes:

```html
<div class="my-class" id="my-id">
  This is a custom div block with a class and an ID.
</div>
```

**Shorthand syntax:**
- `.classname` for classes (can use multiple: `.class1 .class2`)
- `#id-name` for IDs
- Any hyphenated attributes: `data-*`, `aria-*`, `hx-*`, etc.

**HTMX Integration:**
```markdown
{~ button hx-get="/api/users" hx-target="#user-list" hx-swap="innerHTML" ~}
Load Users
{~~}

{~ div #user-list .mt-4 ~}
Users will appear here...
{~~}
```

**Alpine.js Integration:**
```markdown
{~ div x-data="{ open: false }" ~}
  {~ button @click="open = !open" .btn ~}
  Toggle
  {~~}

  {~ div x-show="open" x-transition ~}
  Content revealed!
  {~~}
{~~}
```

**Available HTML Elements:**
- **Block elements:** `div`, `section`, `article`, `aside`, `header`, `footer`, `nav`, `main`, `p`, `span`
- **Void elements:** `hr`, `br`

Paired with powerful libraries like HTMX and Alpine.js, this creates dynamic and interactive interfaces without ever leaving your markdown files.

### Example: SpellBlocks, re-usable Content Components

Spellblocks are reusable content components that can be embedded directly in your markdown content. They provide a powerful way to create rich, interactive content while maintaining the simplicity of markdown syntax.

```markdown
{~ alert type="warning" ~}
Warning: This is an important notice!
{~~}
```

Be sure to include the `{% spellbook_styles %}` tag in your base template if you want to use the built-in styles.

### Theme System

Django Spellbook includes a powerful theme system that lets you configure your entire site's color scheme through Python settings. No CSS knowledge required!

#### Quick Start with Built-in Themes

```python
# settings.py
from django_spellbook.theme import THEMES

# Choose from 9 magical themes
SPELLBOOK_THEME = THEMES['arcane']     # Deep purple magic
# SPELLBOOK_THEME = THEMES['celestial']  # Divine blues and gold
# SPELLBOOK_THEME = THEMES['forest']     # Woodland greens
# SPELLBOOK_THEME = THEMES['ocean']      # Deep sea blues
# SPELLBOOK_THEME = THEMES['phoenix']    # Fire colors
# SPELLBOOK_THEME = THEMES['shadow']     # Monochrome
# SPELLBOOK_THEME = THEMES['enchanted']  # Magical pinks
# SPELLBOOK_THEME = THEMES['pastel']     # Soft colors
```

#### Custom Theme Configuration

```python
# settings.py
SPELLBOOK_THEME = {
    'colors': {
        'primary': '#8B008B',      # Dark magenta
        'secondary': '#4B0082',    # Indigo
        'accent': '#FFD700',       # Gold
        'error': '#DC143C',        # Crimson
        # ... customize any color
    },
    'custom_colors': {
        'magic': '#9D4EDD',        # Use as sb-bg-magic
        'spell': '#C77DFF',        # Use as sb-text-spell
        # ... add your own color names
    }
}
```

Then in your templates:
```html
{% load spellbook_tags %}
<!DOCTYPE html>
<html>
<head>
    {% spellbook_styles %}  <!-- Loads theme + all styles -->
</head>
<body>
    <div class="sb-bg-primary sb-text-white sb-p-4">
        Theme colors work everywhere!
    </div>
</body>
</html>
```

All SpellBlocks and utility classes automatically adapt to your chosen theme. Change one setting, and your entire site updates!

![Example of alert spellblocks](https://i.imgur.com/wRzMKZv.png)

```markdown
{~ card title="Getting Started" footer="Last updated: 2024" ~}

This is the main content of the card.

- Supports markdown
- Can include lists
- And other **markdown** elements

{~~}
```

![Example of card spellblocks](https://i.imgur.com/dzNUgjQ.png)

Those are two examples of built-in Spellblocks. You can also create your own custom Spellblocks by extending the `BasicSpellBlock` class and registering them with the `SpellBlockRegistry`. See the [documentation on Spellblocks](https://django-spellbook.org/docs/Spellblocks/custom-spellblocks/) for more information.

# Usage - Rendering Markdown to HTML within a python script

```python
from django_spellbook.parsers import spellbook_render

def my_view(request):
    markdown_text = """
# Hello World

{~ alert type="warning" ~}
Warning: This is an important notice!
{~~}

This is my content.

{~ card title="Getting Started" footer="Last updated: 2024" ~}

This is the **main content** of the *card*.
{~~}
"""
    html = spellbook_render(markdown_text)
    return HttpResponse(html)
```

> **Note:** The function `render_spellbook_markdown_to_html` is deprecated as of version 0.2.4 and will be removed in version 0.4.0. Please use `spellbook_render` instead.

# Commands

`python manage.py spellbook_md`

This command will process markdown files in the specified directory from `settings.py`, rendering them as HTML and storing them in your app's templates directory. The rendered templates are accessible for further use in Django views, providing seamless markdown-based content management.

Additionally, the command generates a `spellbook_manifest.json` file in each app, which enables automatic sitemap integration (see Sitemap Integration below).

## Settings

To configure the paths and templates used by Django Spellbook, add the following settings to your settings.py:

### Basic Configuration

```python
# settings.py
SPELLBOOK_MD_PATH = BASE_DIR / 'markdown_files'
SPELLBOOK_MD_APP = 'my_app'
```

- `SPELLBOOK_MD_PATH`: Specifies the path where markdown files are stored.
- `SPELLBOOK_MD_APP`: Sets the app where processed markdown files will be saved.
- `SPELLBOOK_MD_BASE_TEMPLATE`: Base template that wraps markdown-rendered content. **Defaults to `'django_spellbook/bases/sidebar_left.html'`** which provides a professional layout with TOC, themes, and responsive design out-of-the-box.

**Using the Default (Recommended for Quick Start):**
```python
# settings.py - minimal configuration uses built-in template automatically
SPELLBOOK_MD_PATH = BASE_DIR / 'docs'
SPELLBOOK_MD_APP = 'my_app'
# No need to specify SPELLBOOK_MD_BASE_TEMPLATE - uses sidebar_left.html by default!
```

**Customizing the Base Template:**
```python
# settings.py - use your own custom base template
SPELLBOOK_MD_BASE_TEMPLATE = 'my_app/sb_base.html'
```

**Opting Out (Raw HTML Only):**
```python
# settings.py - explicitly set to None for no template wrapper
SPELLBOOK_MD_BASE_TEMPLATE = None
```

The base template (whether default or custom) must have a block named `spellbook_md` that will be used to wrap the rendered markdown content. Here is a basic example of a custom base template:

```html
<!-- my_app/sb_base.html -->
{% extends 'base.html' %}
{% load spellbook_tags %}
<!-- extended base.html has a block named 'content' -->
{% block content %}
<div class="spellbook-md">
    <!-- 'spellbook_md' is the required block name -->
    {% block spellbook_md %} {% endblock %}
</div>
{% endblock %}
<!-- extended base.html has a block named 'extra_css' -->
{% block extra_css %}
{% spellbook_styles %}
{% endblock %}
```

#### Multiple Source-Destination Pairs

Django Spellbook supports processing multiple source directories to different destination apps:

```python
# settings.py
SPELLBOOK_MD_PATH = [
    BASE_DIR / 'docs_content',
    BASE_DIR / 'blog_content'
]
SPELLBOOK_MD_APP = [
    'docs_app', 
    'blog_app'
]
```

With this configuration:

- Content from `docs_content` is processed to the `docs_app`
- Content from `blog_content` is processed to the `blog_app`
- Each app maintains its own set of templates, views, and URLs

#### URL Prefixes

Django Spellbook allows you to customize URL prefixes for your markdown content:

```python
# Single source with custom URL prefix
SPELLBOOK_MD_URL_PREFIX = "docs"  # Content at /docs/

# Multiple sources with custom URL prefixes
SPELLBOOK_MD_URL_PREFIX = [
    "documentation",  # First source at /documentation/
    "blog"           # Second source at /blog/
]

```

If not specified:

- For single app configurations: Empty prefix (content at root URL)
- For multiple apps: First app gets empty prefix, others use their app name

## Accessing Your Spellbook Markdown Content

After running the markdown processing command, your content will be organized within your specified app's templates under `templates/spellbook_md/`. These files are created automatically in your app directory based on your `SPELLBOOK_MD_APP` setting.

To make your markdown-rendered pages accessible from the browser, add a path in your main `urls.py`:

```python
# my_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # other paths...
    path('', include('django_spellbook.urls')),  # Mount at root for cleanest URLs
    # Or use a prefix if needed
    # path('content/', include('django_spellbook.urls')),
]
```

### URL Structure Based on Configuration

The URL structure for your content depends on your settings:

#### Single Source Configuration

For a single source with no URL prefix specified:

- `/page-name/`
- `/folder/sub-page/`

With a custom URL prefix:

```python
SPELLBOOK_MD_URL_PREFIX = "docs"
```

- `/docs/page-name/`
- `/docs/folder/sub-page/`

#### Multiple Source Configuration

When using multiple source-destination pairs with custom URL prefixes:

```python
SPELLBOOK_MD_URL_PREFIX = ["docs", "blog"]
```

- `/docs/installation/`
- `/blog/first-post/`

If no URL prefixes are specified, the default behavior gives the first app an empty prefix and uses app names for others:

- `/installation/`  (First app at root)
- `/blog_app/first-post/`  (Second app with app name prefix)

### How Views and URLs Are Generated

When you run the command, Django Spellbook processes all markdown files in the configured source directories. Here's a step-by-step breakdown of how URLs and views are generated:

1. Parsing Markdown Files:
   - Each markdown file is read and converted to HTML using Spellbook's markdown parser.
   - During this step, Spellbook builds a `ProcessedFile` object for each markdown file, which includes details like the original file path, the processed HTML, the template path, and a relative URL.
2. Creating Templates:
   - The processed HTML is saved as a template in the specified app under `templates/spellbook_md/`.
   - If `SPELLBOOK_MD_BASE_TEMPLATE` is set, the generated HTML will be wrapped in an extended base template.
3. Generating Views:
   - For each markdown file, Spellbook generates a corresponding view function.
   - These view functions are added to app-specific view modules (e.g., `views_docs_app.py`).
   - Each view function is named dynamically based on the file's relative path.

   **Example view function for a markdown file at** `articles/guide.md`:

    ```python
    # For single source configuration (django_spellbook/views.py):
    def view_articles_guide(request):
        context = {} # Auto Generated Context for things like metadata and TOC
        return render(request, 'my_app/spellbook_md/articles/guide.html')

    # For multi-source configuration (django_spellbook/views_docs_app.py):
    def articles_guide(request):
        context = {} # App-specific context with TOC
        return render(request, 'docs_app/spellbook_md/articles/guide.html')
    ```

4. Defining URL Patterns:
   - For each view function, Spellbook creates a URL pattern in the app-specific URL module.
   - For multi-source setups, each app gets its own URL module (e.g., `urls_docs_app.py`).
   - The main `urls.py` in django_spellbook includes all app-specific URL modules with their prefixes.
   - URL patterns incorporate the configured URL prefixes from `SPELLBOOK_MD_URL_PREFIX`, or use defaults if not specified.

5. Accessing the Generated URLs and Views:
   - By including `path('content/', include('django_spellbook.urls'))` in your project's main `urls.py`, all your content becomes accessible.
   - With multiple sources, each app's content is neatly organized under its own URL namespace.

## Sitemap Integration

Django Spellbook integrates seamlessly with Django's sitemap framework. When you run `python manage.py spellbook_md`, a manifest file (`spellbook_manifest.json`) is automatically generated in each app, enabling dynamic sitemap generation at request time.

### Setup

**1. Create a sitemaps.py file in your project:**

```python
# myproject/sitemaps.py
from django_spellbook.sitemaps import SpellbookSitemap

sitemaps = {
    'spellbook': SpellbookSitemap,
}
```

**2. Add the sitemap URL to your urls.py:**

```python
# myproject/urls.py
from django.contrib.sitemaps.views import sitemap
from .sitemaps import sitemaps

urlpatterns = [
    # ... your other URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
```

**3. Visit `/sitemap.xml`** - Django automatically generates your sitemap from all Spellbook pages!

### Multi-App Support

`SpellbookSitemap` automatically discovers all apps configured in `SPELLBOOK_MD_APP`. For manual control:

```python
from django_spellbook.sitemaps import SpellbookSitemap

sitemaps = {
    'docs': SpellbookSitemap(app_names=['docs_app']),
    'blog': SpellbookSitemap(app_names=['blog_app']),
}
```

### Mixing with Other Sitemaps

SpellbookSitemap works alongside your existing Django sitemaps:

```python
from django.contrib.sitemaps import Sitemap
from django_spellbook.sitemaps import SpellbookSitemap

class BlogSitemap(Sitemap):
    # Your custom sitemap
    pass

sitemaps = {
    'blog': BlogSitemap,
    'spellbook': SpellbookSitemap,  # Automatically includes all Spellbook pages
}
```

### Customizing Sitemap Metadata

Add frontmatter to your markdown files to control sitemap properties:

```markdown
---
title: User Guide
published: 2025-12-08
modified: 2025-12-15
is_public: true
---

# Your content here
```

- `published` / `modified`: Used for `<lastmod>` in sitemap
- `is_public: false`: Excludes page from sitemap

