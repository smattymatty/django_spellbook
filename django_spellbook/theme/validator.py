"""
Color validation utilities for Django Spellbook's theme system.
"""

import re
from typing import Optional


# Regular expressions for color formats
HEX_COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
RGB_COLOR_PATTERN = re.compile(r'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$')
RGBA_COLOR_PATTERN = re.compile(r'^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([01]?\.?\d*)\s*\)$')

# CSS named colors (common ones)
CSS_NAMED_COLORS = {
    'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure',
    'beige', 'bisque', 'black', 'blanchedalmond', 'blue',
    'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse',
    'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson',
    'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray',
    'darkgrey', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen',
    'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen',
    'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise',
    'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey',
    'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
    'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray',
    'grey', 'green', 'greenyellow', 'honeydew', 'hotpink',
    'indianred', 'indigo', 'ivory', 'khaki', 'lavender',
    'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral',
    'lightcyan', 'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightgreen',
    'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray',
    'lightslategrey', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen',
    'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue',
    'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue',
    'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue',
    'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy',
    'oldlace', 'olive', 'olivedrab', 'orange', 'orangered',
    'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred',
    'papayawhip', 'peachpuff', 'peru', 'pink', 'plum',
    'powderblue', 'purple', 'red', 'rosybrown', 'royalblue',
    'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell',
    'sienna', 'silver', 'skyblue', 'slateblue', 'slategray',
    'slategrey', 'snow', 'springgreen', 'steelblue', 'tan',
    'teal', 'thistle', 'tomato', 'transparent', 'turquoise',
    'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen'
}


def is_valid_hex_color(color: str) -> bool:
    """
    Check if a string is a valid hex color.
    
    Args:
        color: The color string to validate
        
    Returns:
        True if valid hex color, False otherwise
    """
    return bool(HEX_COLOR_PATTERN.match(color))


def is_valid_rgb_color(color: str) -> bool:
    """
    Check if a string is a valid RGB color.
    
    Args:
        color: The color string to validate
        
    Returns:
        True if valid RGB color, False otherwise
    """
    match = RGB_COLOR_PATTERN.match(color)
    if not match:
        return False
    
    # Check that RGB values are in valid range (0-255)
    r, g, b = match.groups()
    return all(0 <= int(val) <= 255 for val in [r, g, b])


def is_valid_rgba_color(color: str) -> bool:
    """
    Check if a string is a valid RGBA color.
    
    Args:
        color: The color string to validate
        
    Returns:
        True if valid RGBA color, False otherwise
    """
    match = RGBA_COLOR_PATTERN.match(color)
    if not match:
        return False
    
    # Check that RGB values are in valid range (0-255)
    r, g, b, a = match.groups()
    if not all(0 <= int(val) <= 255 for val in [r, g, b]):
        return False
    
    # Check alpha value is between 0 and 1
    try:
        alpha = float(a)
        return 0 <= alpha <= 1
    except ValueError:
        return False


def is_valid_css_color(color: str) -> bool:
    """
    Check if a string is a valid CSS named color.
    
    Args:
        color: The color string to validate
        
    Returns:
        True if valid CSS named color, False otherwise
    """
    return color.lower() in CSS_NAMED_COLORS


def is_valid_color(color: str) -> bool:
    """
    Check if a string is any valid CSS color format.
    
    Args:
        color: The color string to validate
        
    Returns:
        True if valid color, False otherwise
    """
    if not color:
        return False
    
    color = color.strip()
    
    return (
        is_valid_hex_color(color) or
        is_valid_rgb_color(color) or
        is_valid_rgba_color(color) or
        is_valid_css_color(color)
    )


def normalize_hex_color(color: str) -> str:
    """
    Normalize a hex color to 6-digit format.
    
    Args:
        color: The hex color string
        
    Returns:
        Normalized hex color (6 digits)
    """
    if not is_valid_hex_color(color):
        raise ValueError(f"Invalid hex color: {color}")
    
    # Remove # and convert to uppercase
    hex_value = color[1:].upper()
    
    # Expand 3-digit hex to 6-digit
    if len(hex_value) == 3:
        hex_value = ''.join(c * 2 for c in hex_value)
    
    return f'#{hex_value}'


def validate_color(color: str) -> str:
    """
    Validate and normalize a color value.
    
    Args:
        color: The color string to validate
        
    Returns:
        The validated color string (normalized if hex)
        
    Raises:
        ValueError: If the color is invalid
    """
    if not color:
        raise ValueError("Color value cannot be empty")
    
    color = color.strip()
    
    # Normalize hex colors
    if color.startswith('#'):
        if is_valid_hex_color(color):
            return normalize_hex_color(color)
        else:
            raise ValueError(f"Invalid hex color format: {color}")
    
    # Validate RGB/RGBA
    if color.startswith('rgb'):
        if is_valid_rgb_color(color) or is_valid_rgba_color(color):
            return color
        else:
            raise ValueError(f"Invalid RGB/RGBA color format: {color}")
    
    # Validate CSS named colors
    if is_valid_css_color(color):
        return color.lower()
    
    # If we get here, it's not a recognized format
    raise ValueError(
        f"Invalid color format: {color}. "
        "Supported formats: hex (#RGB or #RRGGBB), "
        "rgb(r, g, b), rgba(r, g, b, a), or CSS color names."
    )


def get_color_type(color: str) -> Optional[str]:
    """
    Determine the type of a color value.
    
    Args:
        color: The color string
        
    Returns:
        'hex', 'rgb', 'rgba', 'css', or None if invalid
    """
    if not color:
        return None
    
    color = color.strip()
    
    if is_valid_hex_color(color):
        return 'hex'
    elif is_valid_rgba_color(color):
        return 'rgba'
    elif is_valid_rgb_color(color):
        return 'rgb'
    elif is_valid_css_color(color):
        return 'css'
    
    return None