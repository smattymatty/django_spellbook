import datetime
from django.shortcuts import render

# Table of Contents for all views
TOC = {'title': 'root', 'url': '', 'children': {'blocks': {'title': 'blocks', 'url': 'blocks'}, 'djangolike': {'title': 'djangolike', 'url': 'djangolike'}, 'introduction': {'title': 'introduction', 'url': 'introduction'}, 'sb': {'title': 'Sb', 'url': 'sb', 'children': {'meta_toc': {'title': 'meta_toc', 'url': 'sb/meta_toc'}, 'sb_intro': {'title': 'sb_intro', 'url': 'sb/sb_intro'}, 'spellblocks': {'title': 'spellblocks', 'url': 'sb/spellblocks'}}}}}


def view_introduction(request):
    context = {'title': 'introduction', 'created_at': 'datetime.datetime(2024, 11, 10, 3, 29, 58, 8432)', 'updated_at': 'datetime.datetime(2024, 11, 10, 3, 29, 58, 8432)', 'url_path': 'introduction', 'raw_content': '{% div style="padding: 1rem;" %}\n{% enddiv %}\n\nThis website is my personal portfolio, and also a testing ground to learn new technologies within web development. I\'m constantly learning and improving my skills, and I\'m posting my progress here to share with others.\n\nThe **front-end** of this website is deployed through GitHub Pages, ([Repo Here](https://github.com/smattymatty/smattymatty.github.io)), and the **back-end** is hosted on DigitalOcean. \n\nMy go-to tech stack has changed over the years as I\'ve learned more about web development. As new tools came and old tools went, I\'ve found that I\'m able to build more complex and powerful web applications with less code. \n\n# Back End Development\n\n## Django\n\nDjango is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Its built-in admin interface, ORM, and authentication system significantly reduce development time while maintaining security and scalability.\n\nDjango\'s open & friendly community, well-written documentation, and vast supply of tutorials has made it a great option for back end development. Since it is \'batteries included\', it\'s easy to get started with a project, and it\'s a great choice for small to medium sized projects.\n\nKey strengths:\n\n- Automatic admin interface generation\n- Robust security features out of the box\n- Modular architecture which allows for easy extension\n- Highly scalable with built-in caching support and asynchronous tasks\n\nThis content you\'re readingis hosted on a Django project, [github here](https://github.com/smattymatty/portfolio_server/blob/master/B_markdown_files/introduction.md), rendered through \'Django Spellbook\', and deployed on DigitalOcean.\n\nDjango houses one of the largest and friendliest open source communities in the world, which has inspired me to contribute to the ecosystem with my own project, Django Spellbook.\nTODO: Link to Django Spellbook Open Source Library\n\nTODO: Django 5 by example blog posts\n\n```python\n# Example of Django\'s powerful ORM\nfrom django.db import models\n\nclass Book(models.Model):\n    title = models.CharField(max_length=200)\n    author = models.ForeignKey(\'Author\', on_delete=models.CASCADE)\n    published = models.DateField()\n\n    def get_related_books(self):\n        return Book.objects.filter(author=self.author).exclude(id=self.id)\n```\n\n## DigitalOcean\n\nDigitalOcean provides a robust cloud infrastructure that simplifies deployment and scaling. Their App Platform offers:\n\n- Automated deployments from Git\n- Built-in SSL certificate management\n- Automatic horizontal scaling\n- Container registry and Kubernetes support\n\nOne of my favorite features of DigitalOcean is their automated deployments from Git I\'ve been using GitHub actions for a while, so this pairs perfectly with my workflow. I also love how easy it is to manage multiple domains, and `.env` variables, making it easy to test in my own environment, and then deploy to production without having to worry about configuration.\n\n## Linux\n\nThe backbone of modern web hosting, Linux provides:\n\n- Superior process management with systemd\n- Efficient resource utilization\n- Robust containerization support\n- Comprehensive logging and monitoring\n\nI started using Linux in 2019 because I needed access to Docker and Gunicorn, and because I wanted more contol over my system\'s resources in order to properly test and deploy my web applications. I love how customizable Linux is, and it\'s great open source community that provides a lot of great tools that are often on par with, or better than, commercial offerings. Plus, I\'m a huge fan of the Linux philosophy of "Do one thing and do it well", and I think it\'s a great way to build a solid foundation for your web development projects.\n\n# Front End Development\n\n## HTMX\n\nHTMX extends HTML\'s capabilities to create dynamic interfaces without complex JavaScript frameworks. It excels at:\n\n- Ajax requests directly from HTML\n- WebSocket integration\n- Server-Sent Events\n- Dynamic page updates\n\n```html\n<!-- Dynamic content loading with HTMX -->\n<div \n  hx-get="/api/latest-posts" \n  hx-trigger="every 2s" \n  hx-swap="innerHTML">\n  <!-- Content updates every 2 seconds from the server -->\n</div>\n```\n\nThe way HTMX meshes with the simplicity of HTML\'s original design is a game changer. Instead of overly complex JavaScript frameworks, HTMX allows you to create dynamic interfaces without the need for JavaScript. I still like using Vanilla JavaScript for more complex interactions, but HTMX is a great tool for creating simple, dynamic interfaces without the overhead of a full JavaScript framework.\n\nTODO: HTMX-ify your Django Blog\n\n## CSS and HTML\n\nWith modern CSS, building responsive and accessible interfaces is more streamlined:\n\n- Flexbox for arranging elements in flexible layouts, ideal for rows, columns, and aligning items.\n- Custom Properties to create themes that can adapt to dark/light modes or user preferences.\n- Media Queries to ensure content displays well on any device size, with tailored layouts and font adjustments.\n- Pseudoselectors to enhance interactive elements like buttons and links, making them visually engaging.\n\n```css\n/* Flexbox Layout with Media Queries */\n.container {\n  display: flex;\n  flex-wrap: wrap;\n  gap: 1.5rem;\n  padding: 1rem;\n  justify-content: space-around;\n}\n\n@media (max-width: 768px) {\n  .container {\n    flex-direction: column;\n    align-items: center;\n  }\n}\n```\n\nMy introduction to CSS was through Tailwind, which is a utility-first CSS framework that provides a lot of the same features as Bootstrap, but with a much smaller footprint.\n\nLately I find myself using vanilla CSS more and more, now that I have learned more about the language and its capabilities, I enjoy the freedom of creating my own classes and the pseudoselectors to go along with them.\n\n## JavaScript\n\nJavaScript enables complex client-side interactions while maintaining accessibility:\n\n- Async/await for clean asynchronous code\n- Web Components for reusable elements\n- Intersection Observer for performance\n- Service Workers for offline capability\n\n```javascript\n// Modern JavaScript example\nclass CustomElement extends HTMLElement {\n  constructor() {\n    super();\n    this.attachShadow({ mode: "open" });\n  }\n\n  connectedCallback() {\n    this.render();\n  }\n}\n```\n\nTODO: Link to Melvor Mod Contest\nTODO: Simple Arcade Games\n\n---\n\nThis tech stack combines to create web applications that are:\n\n- Highly performant\n- Accessible by default\n- Easy to maintain\n- Scalable for growth\n', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/introduction.html', context)


def view_djangolike(request):
    context = {'title': 'djangolike', 'created_at': 'datetime.datetime(2024, 10, 29, 19, 27, 18, 854969)', 'updated_at': 'datetime.datetime(2024, 10, 29, 19, 27, 18, 854969)', 'url_path': 'djangolike', 'raw_content': 'Regular markdown text here\n\n{% div .custom-class #unique-id data-test="value" %}\nThis is inside a div with:\n\n- custom class\n- unique ID\n- data attribute\n  {% enddiv %}\n\n{% section .hero .bg-primary %}\n\n# Hero Section\n\nSome content here with **bold** and _italic_ text\n{% endsection %}\n\n{% aside .notes #sidebar role="complementary" %}\n\n> Important note\n\n1. First point\n2. Second point\n   {% endaside %}\n\n{% article .blog-post #post-1 data-author="john" %}\n\n## Blog Post Title\n\nRegular paragraph with [link](https://example.com)\n\n- List item 1\n- List item 2\n\n```code\nSome code block\n```\n\n{% endarticle %}\n', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/djangolike.html', context)


def view_blocks(request):
    context = {'title': 'blocks', 'created_at': 'datetime.datetime(2024, 11, 13, 2, 6, 55, 225967)', 'updated_at': 'datetime.datetime(2024, 11, 13, 2, 6, 55, 225967)', 'url_path': 'blocks', 'raw_content': '{~ alert type="warning" ~}\n⚠️ Warning: This is an important notice!\n{~~}\n\n{~ alert type="success" ~}\n✅ Great job! Operation completed successfully.\n{~~}\n\n{~ alert type="danger" ~}\n🚫 Error: Something went wrong!\n{~~}\n\n{~ alert type="info" ~}\nℹ️ Note: Here\'s some useful information.\n{~~}\n\n{~ card class="shadow-sm mb-4" ~}\n\n## Feature Highlight\n\nThis card contains important information about a feature.\n\n- Point 1\n- Point 2\n- Point 3\n\n{~~}\n\n{~ card title="Important Information" footer="Last updated: 2024" class="shadow-lg" ~}\n## Content Section\n\nThis card has both a title and footer with dividers.\n{~~}', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/blocks.html', context)


def view_sb_meta_toc(request):
    context = {'title': 'meta_toc', 'created_at': 'datetime.datetime(2024, 11, 12, 23, 25, 56, 783700)', 'updated_at': 'datetime.datetime(2024, 11, 12, 23, 25, 56, 783700)', 'url_path': 'sb/meta_toc', 'raw_content': '## Context, Custom Meta, and Table of Contents\n\nDjango Spellbook provides a rich context system for your markdown files, allowing you to add metadata and organize your content hierarchically. This is achieved through frontmatter in your markdown files and an automatic table of contents generator.\n\n### Frontmatter and Context\n\nEach markdown file can include YAML frontmatter at the top of the file to specify metadata:\n\n```markdown\n---\ntitle: My Custom Page Title\ntags: [\'django\', \'python\', \'web\']\nis_public: false\ncustom_field: any value you want\n---\n\nYour content starts here\n```\n\nThe frontmatter is parsed and made available in your templates through the SpellbookContext object, which includes:\n\n**Default Fields:**\n\n- `title`: The page title (defaults to filename if not specified in frontmatter)\n- `created_at`: File creation timestamp (defaults to current time if not specified in frontmatter)\n- `url_path`: The relative URL path to the file (based on the directory structure, cannot be changed)\n- `raw_content`: The markdown content without frontmatter\n- `toc`: Table of contents structure (automatically generated)\n\n**Optional Fields (with defaults):**\n\n- `is_public`: Controls visibility (default: True) TODO: hide False pages\n- `tags`: List of tags (default: []) TODO: add tag pages\n- `custom_meta`: Dictionary of additional frontmatter fields\n- `next_page`: Next page URL in sequence (default: None)\n- `prev_page`: Previous page URL in sequence (default: None)\n\n**Example template usage:**\n\n```html\n{% verbatim %}\n<h1>{{ title }}</h1>\n<div class="metadata">\n    <span>Created: {{ created_at|date:"F j, Y" }}</span>\n    <span>Last Updated: {{ updated_at|date:"F j, Y" }}</span>\n    {% if tags %}\n        <div class="tags">\n            {% for tag in tags %}\n                <span class="tag">{{ tag }}</span>\n            {% endfor %}\n        </div>\n    {% endif %}\n</div>\n\n{% if custom_meta %}\n    <div class="custom-meta">\n        {% for key, value in custom_meta.items %}\n            <div>{{ key }}: {{ value }}</div>\n        {% endfor %}\n    </div>\n{% endif %}\n{% endverbatim %}\n```\n\n### Table of Contents\n\nSpellbook automatically generates a table of contents based on your markdown file structure. The TOC is available in all templates through the `toc` context variable:\n\n```html\n{% verbatim %}\n{% load spellbook_tags %}\n<nav class="toc">\n    {% if toc.children %}\n        <ul>\n            {% for section, data in toc.children.items %}\n                <li>\n                    {% if data.url %}\n                        <a href="{% spellbook_url data.url %}">{{ data.title }}</a>\n                    {% else %}\n                        <span>{{ data.title }}</span>\n                    {% endif %}\n                    \n                    {% if data.children %}\n                        <ul>\n                            {% for page, page_data in data.children.items %}\n                                <li>\n                                    <a href="{% spellbook_url page_data.url %}">\n                                        {{ page_data.title }}\n                                    </a>\n                                </li>\n                            {% endfor %}\n                        </ul>\n                    {% endif %}\n                </li>\n            {% endfor %}\n        </ul>\n    {% endif %}\n</nav>\n{% endverbatim %}\n```\n\nThe TOC structure reflects your markdown file organization:\n\n```\nmarkdown_files/\n├── introduction.md\n├── getting-started.md\n└── advanced/\n    ├── configuration.md\n    └── customization.md\n```\n\nThis creates a TOC structure like:\n\n```python\n{\n    \'title\': \'root\',\n    \'url\': \'\',\n    \'children\': {\n        \'introduction\': {\n            \'title\': \'Introduction\',\n            \'url\': \'introduction\'\n        },\n        \'getting-started\': {\n            \'title\': \'Getting Started\',\n            \'url\': \'getting-started\'\n        },\n        \'advanced\': {\n            \'title\': \'Advanced\',\n            \'url\': \'advanced\',\n            \'children\': {\n                \'configuration\': {\n                    \'title\': \'Configuration\',\n                    \'url\': \'advanced/configuration\'\n                },\n                \'customization\': {\n                    \'title\': \'Customization\',\n                    \'url\': \'advanced/customization\'\n                }\n            }\n        }\n    }\n}\n```\n**URL Generation**\n\nTo handle URLs in your templates, use the included `spellbook_tags`:\n\n```html\n{% verbatim %}\n{% load spellbook_tags %}\n<a href="{% spellbook_url \'advanced/configuration\' %}">Configuration</a>\n{% endverbatim %}\n```\n\nThis ensures URLs are properly generated regardless of your URL configuration.\n\nThe `spellbook_url` tag handles URL generation for your content links, ensuring they work correctly with your URL configuration.\n\n### Customizing the Base Template\n\nWhen using `SPELLBOOK_MD_BASE_TEMPLATE`, ensure your base template includes:\n\n- The spellbook_tags loading\n- A spellbook_md block for content\n- TOC rendering if desired\n- Metadata rendering if desired\n\nExample base template:\n\n```html\n{% verbatim %}\n{% load static %}\n{% load spellbook_tags %}\n\n<div class="spellbook-md">\n    <!-- Optional TOC rendering -->\n    <nav class="spellbook-toc">\n        {% include "spellbook/toc.html" %}\n    </nav>\n\n    <!-- Optional Metadata rendering -->\n    <div class="spellbook-metadata">\n        {% include "spellbook/metadata.html" %}\n    </div>\n    \n    <!-- Main content block -->\n    <main class="spellbook-content">\n        {% block spellbook_md %}{% endblock %}\n    </main>\n</div>\n{% endverbatim %}\n```\n\nThis setup provides a consistent layout while maintaining flexibility for customization.\n', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/sb/meta_toc.html', context)


def view_sb_sb_intro(request):
    context = {'title': 'sb_intro', 'created_at': 'datetime.datetime(2024, 11, 7, 21, 29, 24, 80756)', 'updated_at': 'datetime.datetime(2024, 11, 7, 21, 29, 24, 80756)', 'url_path': 'sb/sb_intro', 'raw_content': '# What is Django Spellbook?\n\nDjango Spellbook is a Library of helpful tools, functions, and commands that are designed to feel like they\'re part of Django, with a touch of magic added to your project. It includes components that make handling tasks like markdown parsing more powerful and flexible than standard Django utilities.\n\nIt\'s a collection of tools that I\'ve found useful in my projects, and I hope that you will too.\n\n# Installation\n\nInstall the package with pip:\n`pip install django-spellbook`\n\nThen, add `django_spellbook` to your Django app\'s `INSTALLED_APPS` in `settings.py`:\n~~~python\n# settings.py\nINSTALLED_APPS = [\n    ...,\n    \'django_spellbook\',\n]\n~~~\n# Usage\n## Markdown Parsing and Rendering\n\nDjango Spellbook\'s markdown processor offers a more flexible and Django-like approach to markdown parsing by extending traditional markdown syntax with Django template-like tags.\n\n### Why Use Spellbook\'s Markdown Parser?\n\nThis parser goes beyond the standard markdown syntax by enabling you to include Django-inspired tags directly in your markdown files. This allows for more structured and semantic HTML, especially useful for projects that need finer control over styling and element attributes, like setting classes or IDs directly in markdown. This means you can write markdown that integrates more seamlessly with your Django templates.\n\n### Example: Writing Markdown with Django-like Tags\n\nWith Django Spellbook, you can use special tags directly in your markdown:\n~~~markdown\n{% verbatim %}\n{% div .my-class #my-id %}\nThis is a custom div block with a class and an ID.\n{% enddiv %}\n{% endverbatim %}\n~~~\nThe above will render as HTML with the specified class and ID attributes:\n~~~html\n<div class="my-class" id="my-id">\nThis is a custom div block with a class and an ID.\n</div>\n~~~\nYou aren\'t just limited to class or ID attributes, you can set any attribute you want, and even use HTMX attributes like `hx-get` or `hx-swap`:\n~~~markdown\n{% verbatim %}\n{% button .my-class #my-id hx-get="/api/get-data" hx-swap="outerHTML" %}\nThis is a custom div block with a class, an ID, and HTMX attributes.\n{% endbutton %}\n{% endverbatim %}\n~~~\nThe above will render as HTML with the specified class, ID, and HTMX attributes:\n~~~html\n<button class="my-class" id="my-id" hx-get="/api/get-data" hx-swap="outerHTML">\nThis is a custom div block with a class, an ID, and HTMX attributes.\n</button>\n~~~\nPaired with powerful libraries like HTMX, this can create dynamic and interactive interfaces that are both visually appealing and highly functional without ever having to leave your markdown files.\n\n### Commands\n`python manage.py spellbook_md`\n\nThis command will process markdown files in the specified directory from `settings.py`, rendering them as HTML and storing them in your app’s templates directory. The rendered templates are accessible for further use in Django views, providing seamless markdown-based content management.\n\n### Settings\n\nTo configure the paths and templates used by Django Spellbook, add the following settings to your settings.py:\n\n- `SPELLBOOK_MD_PATH`: Specifies the path where markdown files are stored.\n~~~python\n# settings.py\nSPELLBOOK_MD_PATH = BASE_DIR / \'markdown_files\'\n~~~\n\n- `SPELLBOOK_CONTENT_APP`: Sets the app where processed markdown files will be saved.\n~~~python\n# settings.py\nSPELLBOOK_CONTENT_APP = \'my_app\'\n~~~\n\n- `SPELLBOOK_MD_BASE_TEMPLATE`: If specified, this base template will wrap all markdown-rendered templates, allowing for consistent styling across your markdown content.\n~~~python\n# settings.py\nSPELLBOOK_MD_BASE_TEMPLATE = \'my_app/sb_base.html\'\n~~~\nThe base template must have a block named `spellbook_md` that will be used to wrap the rendered markdown content. Here is a basic example of a base template:\n~~~html\n{% verbatim %}\n<!-- my_app/sb_base.html -->\n{% extends \'base.html\' %}\n<div class="spellbook-md">\n{% block spellbook_md %}\n{% endblock %}\n</div>\n{% endverbatim %}\n~~~\n## Accessing Your Spellbook Markdown Content\n\nAfter running the markdown processing command, your content will be organized within your specified content app’s templates under `templates/spellbook_md/`. These files are created automatically in your app directory based on your `SPELLBOOK_CONTENT_APP` setting.\n\nTo make your markdown-rendered pages accessible from the browser, add a path in your main `urls.py`:\n~~~python\n# my_project/urls.py\nfrom django.contrib import admin\nfrom django.urls import path, include\n\nurlpatterns = [\n    # other paths...\n    path(\'spellbook/\', include(\'django_spellbook.urls\')),\n    # other includes...\n]\n~~~\nThis setup maps your processed markdown files to URLs prefixed with `/spellbook/`, making it easy to access all converted content as if it were part of your Django app. Each markdown file is available at a route based on its relative path in `SPELLBOOK_MD_PATH`, automatically linking your processed markdown content for seamless browsing.\n### How Views and URLs Are Generated\n\nWhen you run the command, Django Spellbook processes all markdown files in the directory specified by `SPELLBOOK_MD_PATH`. Here\'s a step-by-step breakdown of how URLs and views are generated during this process:\n\n1. Parsing Markdown Files:\n\n- Each markdown file is read and converted to HTML using Spellbook\'s markdown parser, which supports Django-like tags for more flexible styling and layout options.\n- During this step, Spellbook builds a `ProcessedFile` object for each markdown file, which includes details like the original file path, the processed HTML, the template path, and a relative URL (derived from the markdown file’s path and name).\n\n2. Creating Templates:\n\n- The processed HTML is saved as a template in the specified content app under `templates/spellbook_md/`. This directory is automatically created if it doesn’t already exist.\n- If `SPELLBOOK_MD_BASE_TEMPLATE` is set, the generated HTML will be wrapped in an extended base template, allowing you to keep a consistent look across your content.\n\n3. Generating Views:\n\n- For each markdown file, Spellbook generates a corresponding view function, which is responsible for rendering the processed HTML template.\n- These view functions are added to `views.py` in the `django_spellbook` app. Each view function is named dynamically based on the file’s relative path, ensuring unique view names that align with the file structure.\n\n**Here’s an example of a generated view function for a markdown file at** `articles/guide.md`:\n~~~python\n# django_spellbook/views.py\ndef view_articles_guide(request):\n    return render(request, \'my_content_app/spellbook_md/articles/guide.html\')\n~~~\n\nTODO: Add context to the view for things like file metadata and table of contents\n\n4. Defining URL Patterns:\n\n- For each view function, Spellbook creates a URL pattern that maps the relative URL of the markdown file to its view.\n- These URL patterns are written to `urls.py` in the `django_spellbook` app, allowing for centralized management of the markdown routes.\n- For example, the markdown file `articles/guide.md` would be available at the URL `spellbook/articles/guide/`, if `spellbook/` is the URL prefix added in your main `urls.py`.\n\n5. Accessing the Generated URLs and Views:\n\n- By including `path(\'spellbook/\', include(\'django_spellbook.urls\'))` in your project’s main `urls.py`, you make all generated URLs accessible under the `spellbook/` prefix.\n- This setup means that each markdown file is automatically served at a unique, human-readable URL based on its path and name.\n', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/sb/sb_intro.html', context)


def view_sb_spellblocks(request):
    context = {'title': 'spellblocks', 'created_at': 'datetime.datetime(2024, 11, 13, 20, 15, 7, 698521)', 'updated_at': 'datetime.datetime(2024, 11, 13, 20, 15, 7, 698521)', 'url_path': 'sb/spellblocks', 'raw_content': '## Spellblocks: Reusable Content Components\n\n### Overview\n\nSpellblocks are reusable content components that can be embedded directly in your markdown content. They provide a powerful way to create rich, interactive content while maintaining the simplicity of markdown syntax.\n\n```markdown\n{~ alert type="warning" ~}\n⚠️ Warning: This is an important notice!\n{~~}\n```\n\n{~ alert type="warning" ~}\n⚠️ Warning: This is an important notice!\n{~~}\n\n**Key Features:**\n\n- Registry System: Automatically discovers and registers blocks from all installed apps\n- Template-Based Rendering: Each block can have its own template for consistent styling\n- Flexible Arguments: Support for custom arguments and content\n- Inheritance System: Easy to extend and create custom blocks\n\n### Using Built-in Blocks\n\n**Alert Block**\n\nThe Alert block is perfect for highlighting important information. It supports multiple types to convey different levels of importance.\n\n```markdown\n{~ alert type="success" ~}\n✅ Operation completed successfully!\n{~~}\n```\n\n{~ alert type="success" ~}\n✅ Operation completed successfully!\n{~~}\n\nAvailable Types:\n\n- `info` (default) For general information\n- `warning` For cautionary or messages\n- `success` For positive or outcomes\n- `danger` For error or failure\n- `primary` For primary or main actions\n- `secondary` For secondary or supporting actions\n\n**Card Block**\n\nThe Card block provides a flexible container for content with optional header and footer sections.\n\n```markdown\n{~ card title="Getting Started" footer="Last updated: 2024" ~}\n\nThis is the main content of the card.\n\n- Supports markdown\n- Can include lists\n- And other **markdown** elements\n\n{~~}\n```\n\n{~ card title="Getting Started" footer="Last updated: 2024" ~}\n\nThis is the main content of the card.\n\n- Supports markdown\n- Can include lists\n- And other **markdown** elements\n\n{~~}\n\nOptional Arguments:\n\n- `title` adds a header with the specified title\n- `footer` adds a footer with the specified content\n- `class` adds additional CSS classes to the card container\n\n### Creating a Custom Block: Basic\n\nThe simplest way to create a custom block is to define its name and template. Here\'s an example of a basic "quote" block:\n\n1. Create your block in `spellblocks.py`:\n\n```python\nfrom django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry\n\n@SpellBlockRegistry.register()\nclass QuoteBlock(BasicSpellBlock):\n    name = \'quote\'\n    template = \'myapp/blocks/quote.html\'\n```\n\n2. Create a template in `myapp/templates/myapp/blocks/quote.html`:\n\n```html\n{% verbatim %}\n<blockquote class="spellbook-quote">\n    {{ content|safe }}\n</blockquote>\n{% endverbatim %}\n```\n\n3. Use the block in your markdown content:\n\n```markdown\n{~ quote ~}\nLife is like a box of chocolates.\n- Forrest Gump\n{~~}\n```\n\nThat\'s it! This basic block will wrap its content in a blockquote element.\n\n### Creating a Custom Block: Advanced\n\nFor more complex functionality, you can add argument validation, error handling, and custom processing. Here\'s an example of a "note" block with different styles:\n\n1. Create the advanced block in `spellblocks.py`:\n\n```python\n@SpellBlockRegistry.register()\nclass NoteBlock(BasicSpellBlock):\n    name = \'note\'\n    template = \'myapp/blocks/note.html\'\n    \n    # Define valid styles and their icons\n    VALID_STYLES = {\n        \'tip\': \'💡\',\n        \'info\': \'ℹ️\',\n        \'important\': \'⚡\',\n        \'note\': \'📝\',\n    }\n    \n    def get_context(self):\n        context = super().get_context()\n        \n        # Validate and process style\n        style = self.kwargs.get(\'style\', \'note\').lower()\n        if style not in self.VALID_STYLES:\n            print(\n                f"Invalid style \'{style}\'. Using \'note\'. "\n                f"Valid styles: {\', \'.join(sorted(self.VALID_STYLES))}"\n            )\n            style = \'note\'\n        \n        # Add title if provided, or use style name\n        title = self.kwargs.get(\'title\', style.title())\n            \n        # Add to context\n        context.update({\n            \'style\': style,\n            \'icon\': self.VALID_STYLES[style],\n            \'title\': title,\n        })\n        \n        return context\n```\n\n2. Create the template in `myapp/templates/myapp/blocks/note.html`:\n\n```html\n{% verbatim %}\n<div class="spellbook-note spellbook-note-{{ style }}">\n    <div class="note-header">\n        <span class="note-icon">{{ icon }}</span>\n        <span class="note-title">{{ title }}</span>\n    </div>\n    <div class="note-content">\n        {{ content|safe }}\n    </div>\n</div>\n{% endverbatim %}\n```\n\n3. Use the block in your markdown content:\n\n```markdown\n{~ note style="tip" title="Pro Tip!" ~}\nYou can use keyboard shortcuts to navigate faster:\n- `Ctrl + S` to save\n- `Ctrl + F` to search\n{~~}\n\n{~ note style="important" ~}\nDon\'t forget to backup your data regularly!\n{~~}\n```\n\nThis advanced block demonstrates several important features:\n\n- *Style Validation*: Checks for valid note styles\n- *Default Values*: Uses \'note\' style if none specified\n- *Custom Icons*: Automatically adds appropriate icons\n- *Optional Title*: Uses custom title or defaults to style name\n- *Error Handling*: Logs warnings for invalid inputs\n- *Markdown Support*: Processes markdown content inside the note', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'A_content/spellbook_md/sb/spellblocks.html', context)
