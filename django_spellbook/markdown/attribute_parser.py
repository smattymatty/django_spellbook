# django_spellbook/markdown/attribute_parser.py

import re
from typing import Dict, List

# --- Regular Expressions for Attribute Parsing ---

# Matches class shortcuts like ".my-class" or ".another_class"
# Allows alphanumeric characters, hyphens, and colons (for Tailwind-like classes)
RE_CLASS = re.compile(r'\.([:\w-]+)')

# Matches ID shortcuts like "#my-id"
# Allows alphanumeric characters and hyphens
RE_ID = re.compile(r'#([\w-]+)')

# Matches standard HTML attributes like name="value" or data-attr='value'
# Handles single or double quotes for values.
# Allows alphanumeric characters, hyphens, and colons in attribute names (e.g., @click, data-*)
RE_ATTR = re.compile(r'([@:\w-]+)=([\'"])(.*?)\2') # Group 3 captures the value without quotes

# --- Parsing Function ---

def parse_attributes(attrs_string: str) -> Dict[str, str]:
    """
    Parses a string containing attribute definitions, including shortcuts.

    Handles:
    - Class shortcuts: `.class-name`
    - ID shortcuts: `#id-name`
    - Standard attributes: `key="value"` or `key='value'`

    Precedence Rules:
    - Explicit `id="..."` attribute overrides any `#id-name` shortcut.
    - Explicit `class="..."` attribute is combined with `.class-name` shortcuts.
      Shortcut classes appear first, followed by classes from the explicit attribute.
    - Only the *first* `#id-name` shortcut found is considered if no explicit
      `id="..."` attribute is present.

    Args:
        attrs_string: The raw string containing attributes from the tag.
                      Example: ' .my-class #my-id data-value="example" class="extra-class" '

    Returns:
        A dictionary where keys are attribute names and values are attribute values.
        Example: {'class': 'my-class extra-class', 'id': 'my-id', 'data-value': 'example'}
    """
    if not attrs_string:
        return {}

    attributes: Dict[str, str] = {}
    shortcut_classes: List[str] = []
    shortcut_id: str | None = None
    explicit_attrs: Dict[str, str] = {}

    # 1. Find all shortcut classes
    shortcut_classes = RE_CLASS.findall(attrs_string)

    # 2. Find the first shortcut ID
    id_match = RE_ID.search(attrs_string)
    if id_match:
        shortcut_id = id_match.group(1)

    # 3. Find all explicit attributes (key="value")
    for match in RE_ATTR.finditer(attrs_string):
        key = match.group(1)
        value = match.group(3) # Use group 3 which excludes the quotes
        explicit_attrs[key] = value

    # 4. Determine final ID
    if 'id' in explicit_attrs:
        attributes['id'] = explicit_attrs['id']
    elif shortcut_id:
        attributes['id'] = shortcut_id

    # 5. Determine final Class list
    final_classes = list(shortcut_classes) # Start with shortcut classes
    if 'class' in explicit_attrs:
        # Split the explicit class string and append to the list
        final_classes.extend(explicit_attrs['class'].split())

    if final_classes:
        # Remove duplicates while preserving order (important for potential CSS cascade)
        ordered_unique_classes = list(dict.fromkeys(final_classes))
        attributes['class'] = ' '.join(ordered_unique_classes)

    # 6. Add all other explicit attributes
    for key, value in explicit_attrs.items():
        # Add only if not 'id' or 'class', as they've been handled
        if key not in ('id', 'class'):
            attributes[key] = value

    return attributes
