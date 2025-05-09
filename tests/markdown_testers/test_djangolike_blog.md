# My Awesome Blog Post - Test Drive

Welcome to this test post! We're going to put our **Django-like tag processor** through its paces.

## Basic Custom Tags

Here's a simple div:

{% div %}
This is paragraph text inside a basic div tag.
{% enddiv %}

Now with some attributes:

{% div class="container mt-4" id="main-content" data-testid="maindiv" %}
This div has several attributes applied directly. It should render with `class="container mt-4"`, `id="main-content"`, and `data-testid="maindiv"`.
{% enddiv %}

- This list should render as a bulleted list.
- Item two.

1. This list should render as a numbered list.
2. Item two.

Let's try the shortcuts:

{% section .hero #hero-section %}
This section uses the `.classname` and `#idname` shortcuts.
It should have `class="hero"` and `id="hero-section"`.

**Markdown** content like *bold* and *italic* should work perfectly fine inside these custom tags.

- As should lists.
- Item two.

```python
# And code blocks too! (Using double backticks)
print("Hello from inside a custom tag")
```

This section also spans multiple paragraphs (Markdown blocks).
{% endsection %}

## Preserving Django Tags

We need to make sure standard Django tags are left alone for the Django template engine.

### Inline Tags

`Let's link to a static asset`: {% static 'css/blog_styles.css' %}
`And here's a dynamic URL:` {% url 'post_detail' slug='test-drive-post' %}
We can even include another template snippet: {% include 'includes/sidebar.html' %}

These should appear wrapped in `<django-tag>` elements.

### Block Tags

Django block tags like `if` and `for` should also be preserved.

{% if user.is_authenticated %}
This content is only shown to logged-in users.
{% elif user.is_anonymous %}  
This content is for anonymous users.
{% else %}
This content is for anonymous users. Please {% url 'login' %} or {% url 'signup' %}.
{% endif %}

## Nesting and Mixing

Let's try nesting our custom tags and mixing them with Django tags.

{% article #post-body %}

## Sub-heading Inside Article

  This is the main article content.

  More *article* **text** here. Now for an aside:

  {% aside .pull-quote %}
    This is an aside (pull quote) nested within the article.
    It might contain *simple* formatting.
  {% endaside %}

  Final paragraph of the article.
{% endarticle %}

This concludes our test document. Let's see how it renders!

---

Final bit of text after all tags.
