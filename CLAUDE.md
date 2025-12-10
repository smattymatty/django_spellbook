## Testing

`python manage.py test` - this is important because its a django app that required django settings and django startup.

## Code

The main code resides in `/django_spellbook/`

- blocks (registering/rendering spellblocks)
- management (python manage.py commands)
- markdown (main rendering engine)
- static (holds our CSS, JS, and SVG files)
- templates (holds component-like HTML files to be rendered by django for metadata, toc, bases, blocks, etc.)
- templatetags (the tags used in templates to render components)
- theme (module for generating, rendering, and prebuilt themes)

