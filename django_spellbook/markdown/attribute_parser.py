# django_spellbook/markdown/attribute_parser.py

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# --- Regular Expressions for Attribute Parsing ---
# Shorthand syntax patterns (CSS-style)
RE_CLASS = re.compile(r'\.([:\w-]+)')
RE_ID = re.compile(r'#([\w-]+)')
RE_ATTR = re.compile(r'([@:\w-]+)=([\'"])(.*?)\2')

# --- Regex for SpellBlock Arguments ---
# Matches key="value", key='value', key=value_no_quotes, or flag
# Supports Alpine.js (@click), Vue (:bind), and regular attributes
SPELLBLOCK_ARG_PATTERN = re.compile(
    r"""
    (?P<key>[@:a-zA-Z_][\w-]*) # Key name (can start with @, :, letter, or _)
    (?: # Optional equals and value part
        \s*=\s* # Equals sign with optional whitespace
        (?: # Group for different value types
            "(?P<d_quoted_value>[^"]*?)" | # Double-quoted value
            '(?P<s_quoted_value>[^']*?)' | # Single-quoted value
            (?P<unquoted_value>[^\s"'=<>`]+)  # Unquoted value
        )
    )? # The entire equals and value part is optional (for flags)
    """,
    re.VERBOSE
)

def parse_shorthand_and_explicit_attributes(
    raw_args_str: str,
    reporter: Optional[Any] = None
) -> Dict[str, str]:
    """
    Parses SpellBlock arguments supporting both shorthand and explicit syntax.

    Shorthand syntax:
        .classname - CSS-style class
        #id-name - CSS-style ID

    Explicit syntax:
        key="value" - Double-quoted
        key='value' - Single-quoted
        key=value - Unquoted
        flag - Boolean flag (key without value)

    Merging rules:
        - Classes: Shorthand classes come first, explicit classes append
        - IDs: Explicit ID wins over shorthand (logs warning if both present)
        - Other attributes: Pass through as-is

    Args:
        raw_args_str: Raw argument string from SpellBlock tag
        reporter: Optional reporter for logging warnings

    Returns:
        Dictionary of parsed attributes

    Examples:
        >>> parse_shorthand_and_explicit_attributes('.my-class #my-id')
        {'class': 'my-class', 'id': 'my-id'}

        >>> parse_shorthand_and_explicit_attributes('.c1 .c2 class="c3"')
        {'class': 'c1 c2 c3'}

        >>> parse_shorthand_and_explicit_attributes('hx-get="/api" hx-target="#result"')
        {'hx-get': '/api', 'hx-target': '#result'}
    """
    if not raw_args_str or not raw_args_str.strip():
        return {}

    # Step 1: Save quoted strings temporarily to avoid modifying their contents
    quoted_strings = []
    def save_quoted(match):
        quoted_strings.append(match.group(0))
        return f'__QUOTED_{len(quoted_strings)-1}__'

    # Create version with placeholders for quoted strings
    args_with_placeholders = re.sub(r'"[^"]*"|\'[^\']*\'', save_quoted, raw_args_str)

    # Step 2: Parse shorthand syntax (.class, #id) from string with placeholders
    # This prevents seeing #result inside hx-target="#result"
    shorthand_attrs = {}

    # Parse shorthand classes
    shorthand_classes = RE_CLASS.findall(args_with_placeholders)
    if shorthand_classes:
        shorthand_attrs['class'] = ' '.join(shorthand_classes)

    # Parse shorthand ID
    id_match = RE_ID.search(args_with_placeholders)
    if id_match:
        shorthand_attrs['id'] = id_match.group(1)

    # Step 3: Remove shorthand tokens for explicit parsing
    # Now remove shorthand tokens (they're only outside quotes)
    args_cleaned = RE_CLASS.sub('', args_with_placeholders)
    args_cleaned = RE_ID.sub('', args_cleaned)

    # Restore quoted strings
    args_without_shorthand = args_cleaned
    for i, quoted in enumerate(quoted_strings):
        args_without_shorthand = args_without_shorthand.replace(f'__QUOTED_{i}__', quoted)

    # Step 4: Parse explicit syntax (key="value") from cleaned string
    explicit_attrs: Dict[str, str] = {}

    for match in SPELLBLOCK_ARG_PATTERN.finditer(args_without_shorthand):
        key = match.group("key")

        d_quoted_val = match.group("d_quoted_value")
        s_quoted_val = match.group("s_quoted_value")
        unquoted_val = match.group("unquoted_value")

        val_to_assign = None
        was_key_value_pair = False

        if d_quoted_val is not None:
            val_to_assign = d_quoted_val
            was_key_value_pair = True
        elif s_quoted_val is not None:
            val_to_assign = s_quoted_val
            was_key_value_pair = True
        elif unquoted_val is not None:
            val_to_assign = unquoted_val
            was_key_value_pair = True

        if was_key_value_pair:
            explicit_attrs[key] = val_to_assign
        else:
            # Flag (boolean attribute)
            explicit_attrs[key] = key

    # Step 5: Merge attributes
    merged_attrs: Dict[str, str] = {}

    # Handle ID - explicit wins over shorthand
    if 'id' in explicit_attrs:
        merged_attrs['id'] = explicit_attrs['id']
        if 'id' in shorthand_attrs and shorthand_attrs['id'] != explicit_attrs['id']:
            if reporter:
                reporter.warning(
                    f"ID conflict: Explicit id='{explicit_attrs['id']}' overrides "
                    f"shorthand #{shorthand_attrs['id']}"
                )
            logger.warning(
                f"ID conflict in attributes: explicit '{explicit_attrs['id']}' "
                f"overrides shorthand '#{shorthand_attrs['id']}'"
            )
    elif 'id' in shorthand_attrs:
        merged_attrs['id'] = shorthand_attrs['id']

    # Handle class - concatenate shorthand + explicit
    class_list = []
    if 'class' in shorthand_attrs:
        class_list.extend(shorthand_attrs['class'].split())
    if 'class' in explicit_attrs:
        class_list.extend(explicit_attrs['class'].split())

    if class_list:
        # Remove duplicates while preserving order
        merged_attrs['class'] = ' '.join(dict.fromkeys(class_list))

    # Add all other explicit attributes
    for key, value in explicit_attrs.items():
        if key not in ('id', 'class'):
            merged_attrs[key] = value

    # Add any other shorthand attributes (currently none besides class/id)
    for key, value in shorthand_attrs.items():
        if key not in ('id', 'class') and key not in merged_attrs:
            merged_attrs[key] = value

    return merged_attrs


def parse_spellblock_style_attributes(raw_args_str: str, reporter: Optional[Any] = None) -> Dict[str, str]:
    """
    Main entry point for parsing SpellBlock attributes.
    Now supports both shorthand (.class #id) and explicit (key="value") syntax.

    This is a wrapper around parse_shorthand_and_explicit_attributes for backward compatibility.

    Args:
        raw_args_str: Raw argument string from SpellBlock tag
        reporter: Optional reporter for logging

    Returns:
        Dictionary of parsed attributes
    """
    return parse_shorthand_and_explicit_attributes(raw_args_str, reporter)


def parse_attributes(attrs_string: str) -> Dict[str, str]:
    # ... (your existing code for this function) ...
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