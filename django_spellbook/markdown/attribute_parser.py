# django_spellbook/markdown/attribute_parser.py

import re
from typing import Dict, List, Optional, Any # Add Optional, Any
import logging # For potential logging within the util

logger = logging.getLogger(__name__) # Optional: if you want logging from this file

# --- Regular Expressions for Attribute Parsing ---
# (Your existing RE_CLASS, RE_ID, RE_ATTR for parse_attributes remain here)
RE_CLASS = re.compile(r'\.([:\w-]+)')
RE_ID = re.compile(r'#([\w-]+)')
RE_ATTR = re.compile(r'([@:\w-]+)=([\'"])(.*?)\2')


# --- New Regex for SpellBlock Arguments ---
# This pattern is designed for the SpellBlock argument syntax:
# key="value", key='value', key=value_no_quotes, flag
SPELLBLOCK_ARG_PATTERN = re.compile(
    r"""
    (?P<key>[a-zA-Z_][\w-]*) # Key name
    (?: # Optional equals and value part
        \s*=\s* # Equals sign, surrounded by optional whitespace
        (?: # Group for different value types
            "(?P<d_quoted_value>[^"]*?)" | # Double-quoted value (content in d_quoted_value)
            '(?P<s_quoted_value>[^']*?)' | # Single-quoted value (content in s_quoted_value)
            (?P<unquoted_value>[^\s"'=<>`]+)  # Unquoted value
        )
    )? # The entire equals and value part is optional (for flags)
    """,
    re.VERBOSE
)

def parse_spellblock_style_attributes(raw_args_str: str, reporter: Optional[Any] = None) -> Dict[str, str]:
    """
    Parses a raw string of SpellBlock-style arguments into a dictionary.
    Handles: key="value", key='value', key=value, flag.
    Ensures empty string values like key="" are parsed as {'key': ''}.
    """
    kwargs: Dict[str, str] = {}
    if not raw_args_str or not raw_args_str.strip():
        return kwargs

    for match in SPELLBLOCK_ARG_PATTERN.finditer(raw_args_str):
        key = match.group("key")
        
        d_quoted_val = match.group("d_quoted_value")
        s_quoted_val = match.group("s_quoted_value")
        unquoted_val = match.group("unquoted_value")

        val_to_assign = None
        was_key_value_pair = False

        if d_quoted_val is not None:
            val_to_assign = d_quoted_val  # Correctly captures empty string ''
            was_key_value_pair = True
        elif s_quoted_val is not None:
            val_to_assign = s_quoted_val  # Correctly captures empty string ''
            was_key_value_pair = True
        elif unquoted_val is not None:
            val_to_assign = unquoted_val
            was_key_value_pair = True
        
        if was_key_value_pair:
            # This check is crucial: val_to_assign can be an empty string '', which is NOT None.
            if val_to_assign is not None: # This check is a bit redundant if was_key_value_pair is True and regex ensures a value group matched.
                                            # But good for safety. It will be true if val_to_assign is ''.
                kwargs[key] = val_to_assign
                if key == "empty_val_arg" or (key == "key" and raw_args_str == 'key=""'): # For specific debugging
                    print(f"UTIL PARSER DBG ({key}): Added to kwargs: {key}='{kwargs[key]}'")
            # No specific warning here for "val was None" if it was a key-value because regex should ensure value part.
        else:
            # If no value part was matched with an '=', it's a flag
            # (and the key itself wasn't empty)
            kwargs[key] = key # Assign key name as value for flags

    # This warning is useful if the whole string didn't yield any kwargs
    # despite being non-empty, indicating a potential wholesale syntax error.
    if not kwargs and raw_args_str.strip(): # pragma: no cover
        if reporter: # TODO: Add proper testing for reporter in parse_spellblock_style_attributes
            reporter.warning(f"Could not parse any arguments from string (via util): '{raw_args_str}'. Please check syntax.")
        logger.warning(f"Argument parsing produced no kwargs from non-empty string (via util): '{raw_args_str}'")

    return kwargs


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