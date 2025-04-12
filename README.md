# What is Django Spellbook?

Django Spellbook is a Library of helpful tools, functions, and commands that are designed to feel like they're part of Django, with a touch of magic added to your project. It includes components that make handling tasks like markdown parsing more powerful and flexible than standard Django utilities.

It's a collection of tools that I've found useful in my projects, and I hope that you will too.

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

# Usage

## Markdown Parsing and Rendering

Django Spellbook's markdown processor offers a more flexible and Django-like approach to markdown parsing by extending traditional markdown syntax with Django template-like tags and blocks of reusable content components.

### Why Use Spellbook's Markdown Parser?

This parser goes beyond the standard markdown syntax by enabling you to include Django-inspired tags directly in your markdown files. This allows for more structured and semantic HTML, especially useful for projects that need finer control over styling and element attributes, like setting classes or IDs directly in markdown. This means you can write markdown that integrates more seamlessly with your Django templates.

### Example: Writing Markdown with Django-like Tags

With Django Spellbook, you can use special tags directly in your markdown:

```markdown
{% div .my-class #my-id %}
This is a custom div block with a class and an ID.
{% enddiv %}
```

The above will render as HTML with the specified class and ID attributes:

```html
<div class="my-class" id="my-id">
  This is a custom div block with a class and an ID.
</div>
```

**Note:** You aren't just limited to class or ID attributes, you can set any attribute you want. `{% div test="value" %}` will render as `<div test="value">`.

Paired with powerful libraries like HTMX, this can create dynamic and interactive interfaces that are both visually appealing and highly functional without ever having to leave your markdown files.

### Example: SpellBlocks, re-usable Content Components

Spellblocks are reusable content components that can be embedded directly in your markdown content. They provide a powerful way to create rich, interactive content while maintaining the simplicity of markdown syntax.

```markdown
{~ alert type="warning" ~}
Warning: This is an important notice!
{~~}
```

Be sure to include the `{% spellbook_styles %}` tag in your base template if you want to use the built-in styles.

IMAGE INCOMING

```markdown
{~ card title="Getting Started" footer="Last updated: 2024" ~}

This is the main content of the card.

- Supports markdown
- Can include lists
- And other **markdown** elements

{~~}
```

IMAGE INCOMING

Those are two examples of built-in Spellblocks. You can also create your own custom Spellblocks by extending the `BasicSpellBlock` class and registering them with the `SpellBlockRegistry`. See the [documentation on Spellblocks](https://django-spellbook.org/docs/Markdown/spellblocks) for more information.

### Commands

`python manage.py spellbook_md`

This command will process markdown files in the specified directory from `settings.py`, rendering them as HTML and storing them in your app's templates directory. The rendered templates are accessible for further use in Django views, providing seamless markdown-based content management.

### Settings

To configure the paths and templates used by Django Spellbook, add the following settings to your settings.py:

#### Basic Configuration

```python
# settings.py
SPELLBOOK_MD_PATH = BASE_DIR / 'markdown_files'
SPELLBOOK_MD_APP = 'my_app'
```

> **Note:** `SPELLBOOK_CONTENT_APP` is deprecated. Use `SPELLBOOK_MD_APP` instead.

- `SPELLBOOK_MD_PATH`: Specifies the path where markdown files are stored.
- `SPELLBOOK_MD_APP`: Sets the app where processed markdown files will be saved.
- `SPELLBOOK_MD_BASE_TEMPLATE`: If specified, this base template will wrap all markdown-rendered templates, allowing for consistent styling across your markdown content.

```python
# settings.py
SPELLBOOK_MD_BASE_TEMPLATE = 'my_app/sb_base.html'
```

The base template must have a block named `spellbook_md` that will be used to wrap the rendered markdown content. Here is a basic example of a base template:

```html
<!-- my_app/sb_base.html -->
{% extends 'base.html' %}
<div class="spellbook-md">{% block spellbook_md %} {% endblock %}</div>
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

## Accessing Your Spellbook Markdown Content

After running the markdown processing command, your content will be organized within your specified app's templates under `templates/spellbook_md/`. These files are created automatically in your app directory based on your `SPELLBOOK_MD_APP` setting.

To make your markdown-rendered pages accessible from the browser, add a path in your main `urls.py`:

```python
# my_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # other paths...
    path('content/', include('django_spellbook.urls')),
    # other includes...
]
```

### Single Source Configuration

For a single source configuration, this will make your content available at paths like:
- `/content/page-name/`
- `/content/folder/sub-page/`

### Multiple Source Configuration

When using multiple source-destination pairs, your content will be organized under app-specific prefixes:
- `/content/docs_app/installation/`
- `/content/blog_app/first-post/`

Each app's content gets its own URL namespace based on the app name, ensuring no conflicts between content from different sources.

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

5. Accessing the Generated URLs and Views:

- By including `path('content/', include('django_spellbook.urls'))` in your project's main `urls.py`, all your content becomes accessible.
- With multiple sources, each app's content is neatly organized under its own URL namespace.