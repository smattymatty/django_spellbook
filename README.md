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
]
```

# Usage

## Markdown Parsing and Rendering

Django Spellbook's markdown processor offers a more flexible and Django-like approach to markdown parsing by extending traditional markdown syntax with Django template-like tags.

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

You aren't just limited to class or ID attributes, you can set any attribute you want.

Paired with powerful libraries like HTMX, this can create dynamic and interactive interfaces that are both visually appealing and highly functional without ever having to leave your markdown files.

### Example: SpellBlocks, re-usable Content Components

Spellblocks are reusable content components that can be embedded directly in your markdown content. They provide a powerful way to create rich, interactive content while maintaining the simplicity of markdown syntax.

```markdown
{~ alert type="warning" ~}
Warning: This is an important notice!
{~~}
```

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

Those are two examples of built-in Spellblocks. You can also create your own custom Spellblocks by extending the `BasicSpellBlock` class and registering them with the `SpellBlockRegistry`. See the [documentation on Spellblocks](google.com) for more information.

### Commands

`python manage.py spellbook_md`

This command will process markdown files in the specified directory from `settings.py`, rendering them as HTML and storing them in your app’s templates directory. The rendered templates are accessible for further use in Django views, providing seamless markdown-based content management.

### Settings

To configure the paths and templates used by Django Spellbook, add the following settings to your settings.py:

- `SPELLBOOK_MD_PATH`: Specifies the path where markdown files are stored.

```python
# settings.py
SPELLBOOK_MD_PATH = BASE_DIR / 'markdown_files'
```

- `SPELLBOOK_CONTENT_APP`: Sets the app where processed markdown files will be saved.

```python
# settings.py
SPELLBOOK_CONTENT_APP = 'my_app'
```

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

## Accessing Your Spellbook Markdown Content

After running the markdown processing command, your content will be organized within your specified content app’s templates under `templates/spellbook_md/`. These files are created automatically in your app directory based on your `SPELLBOOK_CONTENT_APP` setting.

To make your markdown-rendered pages accessible from the browser, add a path in your main `urls.py`:

```python
# my_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # other paths...
    path('spellbook/', include('django_spellbook.urls')),
    # other includes...
]
```

This setup maps your processed markdown files to URLs prefixed with `/spellbook/`, making it easy to access all converted content as if it were part of your Django app. Each markdown file is available at a route based on its relative path in `SPELLBOOK_MD_PATH`, automatically linking your processed markdown content for seamless browsing.

### How Views and URLs Are Generated

When you run the command, Django Spellbook processes all markdown files in the directory specified by `SPELLBOOK_MD_PATH`. Here's a step-by-step breakdown of how URLs and views are generated during this process:

1. Parsing Markdown Files:

- Each markdown file is read and converted to HTML using Spellbook's markdown parser, which supports Django-like tags for more flexible styling and layout options.
- During this step, Spellbook builds a `ProcessedFile` object for each markdown file, which includes details like the original file path, the processed HTML, the template path, and a relative URL (derived from the markdown file’s path and name).

2. Creating Templates:

- The processed HTML is saved as a template in the specified content app under `templates/spellbook_md/`. This directory is automatically created if it doesn’t already exist.
- If `SPELLBOOK_MD_BASE_TEMPLATE` is set, the generated HTML will be wrapped in an extended base template, allowing you to keep a consistent look across your content.

3. Generating Views:

- For each markdown file, Spellbook generates a corresponding view function, which is responsible for rendering the processed HTML template.
- These view functions are added to `views.py` in the `django_spellbook` app. Each view function is named dynamically based on the file’s relative path, ensuring unique view names that align with the file structure.

**Here’s an example of a generated view function for a markdown file at** `articles/guide.md`:

```python
# django_spellbook/views.py
def view_articles_guide(request):
    context = {} # Auto Generated Context for things like metadata and TOC
    return render(request, 'my_content_app/spellbook_md/articles/guide.html')
```

4. Defining URL Patterns:

- For each view function, Spellbook creates a URL pattern that maps the relative URL of the markdown file to its view.
- These URL patterns are written to `urls.py` in the `django_spellbook` app, allowing for centralized management of the markdown routes.
- For example, the markdown file `articles/guide.md` would be available at the URL `spellbook/articles/guide/`, if `spellbook/` is the URL prefix added in your main `urls.py`.

5. Accessing the Generated URLs and Views:

- By including `path('spellbook/', include('django_spellbook.urls'))` in your project’s main `urls.py`, you make all generated URLs accessible under the `spellbook/` prefix.
- This setup means that each markdown file is automatically served at a unique, human-readable URL based on its path and name.
