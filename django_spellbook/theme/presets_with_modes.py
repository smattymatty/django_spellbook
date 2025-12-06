"""
Built-in theme presets with light/dark mode support for Django Spellbook.
"""

from typing import Dict, Any, Optional


# Built-in theme presets with light and dark modes
THEMES_WITH_MODES = {
    'default': {
        'name': 'default',
        'modes': {
            'light': {
                'colors': {
                    # Core semantic colors
                    'primary': '#3b82f6',
                    'secondary': '#6b7280',
                    'accent': '#f59e0b',
                    'neutral': '#2563eb',
                    'error': '#dc2626',
                    'warning': '#f59e0b',
                    'success': '#16a34a',
                    'info': '#2563eb',
                    # Extended colors
                    'emphasis': '#8b5cf6',
                    'subtle': '#f3f4f6',
                    'distinct': '#06b6d4',
                    'aether': '#c026d3',
                    'artifact': '#a16207',
                    'sylvan': '#3f6212',
                    'danger': '#a80000',
                    # System colors for light mode
                    'background': '#ffffff',
                    'surface': '#f9fafb',
                    'text': '#1f2937',
                    'text-secondary': '#6b7280',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    # Core semantic colors (adjusted for dark mode)
                    'primary': '#60a5fa',  # Brighter blue
                    'secondary': '#9ca3af',  # Lighter gray
                    'accent': '#fbbf24',  # Brighter amber
                    'neutral': '#3b82f6',
                    'error': '#ef4444',
                    'warning': '#fbbf24',
                    'success': '#22c55e',
                    'info': '#3b82f6',
                    # Extended colors
                    'emphasis': '#a78bfa',
                    'subtle': '#1f2937',
                    'distinct': '#22d3ee',
                    'aether': '#d946ef',
                    'artifact': '#ca8a04',
                    'sylvan': '#4ade80',
                    'danger': '#dc2626',
                    # System colors for dark mode
                    'background': '#0f0f0f',
                    'surface': '#1a1a1a',
                    'text': '#f3f4f6',
                    'text-secondary': '#9ca3af',
                },
                'generate_variants': True,
            }
        }
    },
    
    'arcane': {
        'name': 'arcane',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#9D4EDD',      # Deep purple magic
                    'secondary': '#240046',    # Midnight purple
                    'accent': '#FFB700',       # Golden spell glow
                    'neutral': '#3C096C',      # Dark mystic purple
                    'error': '#D00000',        # Blood magic red
                    'warning': '#FFAA00',      # Amber warning
                    'success': '#7FB800',      # Nature spell green
                    'info': '#7209B7',         # Arcane knowledge
                    'emphasis': '#C77DFF',     # Light magic purple
                    'subtle': '#F9F5FF',       # Very light purple
                    'distinct': '#E0AAFF',     # Ethereal lavender
                    'aether': '#F72585',       # Pink magical energy
                    'artifact': '#FFD60A',     # Ancient gold
                    'sylvan': '#55A630',       # Forest magic
                    'danger': '#9D0208',       # Dark curse red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#F9F5FF',
                    'text': '#240046',
                    'text-secondary': '#5A0A8C',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#B57BFF',      # Brighter purple for dark
                    'secondary': '#E0AAFF',    # Light purple
                    'accent': '#FFD60A',       # Golden spell glow
                    'neutral': '#7209B7',      # Purple
                    'error': '#FF6B6B',        # Bright red
                    'warning': '#FFC947',      # Bright amber
                    'success': '#8FE1A2',      # Light green
                    'info': '#9D4EDD',         # Purple info
                    'emphasis': '#E0AAFF',     # Light purple
                    'subtle': '#1A0033',       # Very dark purple
                    'distinct': '#F7C8FF',     # Very light purple
                    'aether': '#FF6BB5',       # Bright pink
                    'artifact': '#FFE45E',     # Bright gold
                    'sylvan': '#7FB800',       # Bright green
                    'danger': '#FF6B6B',       # Bright red
                    # System colors
                    'background': '#0A0015',   # Very dark purple
                    'surface': '#1A0033',      # Dark purple
                    'text': '#F0E6FF',         # Light purple
                    'text-secondary': '#C77DFF',
                },
                'generate_variants': True,
            }
        }
    },
    
    'celestial': {
        'name': 'celestial',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#4CC9F0',      # Sky blue
                    'secondary': '#7209B7',    # Deep purple
                    'accent': '#F7E60F',       # Sun yellow
                    'neutral': '#CAD2C5',      # Cloud gray
                    'error': '#F07167',        # Sunset red
                    'warning': '#FFA62B',      # Orange
                    'success': '#8FE1A2',      # Light green
                    'info': '#4361EE',         # Deep blue
                    'emphasis': '#A663CC',     # Purple
                    'subtle': '#F7F7FF',       # Almost white
                    'distinct': '#B4E7FC',     # Light blue
                    'aether': '#E0AAFF',       # Light purple
                    'artifact': '#FFD23F',     # Gold
                    'sylvan': '#95D5B2',       # Light green
                    'danger': '#D62828',       # Red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#F0F8FF',      # Alice blue
                    'text': '#1A237E',         # Deep blue
                    'text-secondary': '#4361EE',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#7DD3FC',      # Bright sky blue
                    'secondary': '#C084FC',    # Light purple
                    'accent': '#FEF08A',       # Light yellow
                    'neutral': '#64748B',      # Gray
                    'error': '#FCA5A5',        # Light red
                    'warning': '#FED7AA',      # Light orange
                    'success': '#BBF7D0',      # Light green
                    'info': '#93C5FD',         # Light blue
                    'emphasis': '#E9D5FF',     # Very light purple
                    'subtle': '#1E293B',       # Dark gray
                    'distinct': '#DBEAFE',     # Very light blue
                    'aether': '#F3E8FF',       # Very light purple
                    'artifact': '#FEF3C7',     # Light yellow
                    'sylvan': '#D1FAE5',       # Very light green
                    'danger': '#FCA5A5',       # Light red
                    # System colors
                    'background': '#0F172A',   # Very dark blue
                    'surface': '#1E293B',      # Dark blue gray
                    'text': '#E0F2FE',         # Light blue
                    'text-secondary': '#BAE6FD',
                },
                'generate_variants': True,
            }
        }
    },
    
    'forest': {
        'name': 'forest',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#2d5016',      # Deep forest green
                    'secondary': '#3e2723',    # Dark brown
                    'accent': '#ff6f00',       # Autumn orange
                    'neutral': '#5d4037',      # Brown
                    'error': '#b71c1c',        # Deep red
                    'warning': '#ff6f00',      # Orange
                    'success': '#1b5e20',      # Green
                    'info': '#004d40',         # Teal
                    'emphasis': '#4a148c',     # Purple
                    'subtle': '#efebe9',       # Light brown
                    'distinct': '#006064',     # Dark cyan
                    'aether': '#6a1b9a',       # Purple
                    'artifact': '#bf360c',     # Deep orange
                    'sylvan': '#33691e',       # Olive green
                    'danger': '#880e4f',       # Maroon
                    # System colors
                    'background': '#ffffff',
                    'surface': '#f5f5dc',      # Beige
                    'text': '#1a1a1a',
                    'text-secondary': '#3e2723',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#66bb6a',      # Light green
                    'secondary': '#8d6e63',    # Light brown
                    'accent': '#ffb74d',       # Light orange
                    'neutral': '#8d6e63',      # Light brown
                    'error': '#ef5350',        # Light red
                    'warning': '#ffb74d',      # Light orange
                    'success': '#66bb6a',      # Light green
                    'info': '#4db6ac',         # Light teal
                    'emphasis': '#ab47bc',     # Light purple
                    'subtle': '#263238',       # Dark gray
                    'distinct': '#4dd0e1',     # Light cyan
                    'aether': '#ba68c8',       # Light purple
                    'artifact': '#ff8a65',     # Light orange
                    'sylvan': '#9ccc65',       # Light olive
                    'danger': '#ec407a',       # Light pink
                    # System colors
                    'background': '#0a0a0a',
                    'surface': '#1a1a1a',
                    'text': '#e8f5e9',         # Light green
                    'text-secondary': '#a5d6a7',
                },
                'generate_variants': True,
            }
        }
    },
    
    'ocean': {
        'name': 'ocean',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#006994',      # Deep ocean blue
                    'secondary': '#01579b',    # Navy blue
                    'accent': '#00acc1',       # Cyan
                    'neutral': '#455a64',      # Blue gray
                    'error': '#d32f2f',        # Red
                    'warning': '#ffa000',      # Amber
                    'success': '#00796b',      # Teal
                    'info': '#0277bd',         # Light blue
                    'emphasis': '#4527a0',     # Deep purple
                    'subtle': '#e0f7fa',       # Very light cyan
                    'distinct': '#00bcd4',     # Cyan
                    'aether': '#7b1fa2',       # Purple
                    'artifact': '#ff8f00',     # Amber
                    'sylvan': '#2e7d32',       # Green
                    'danger': '#c62828',       # Deep red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#e0f7fa',      # Light cyan
                    'text': '#01579b',
                    'text-secondary': '#0277bd',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#4fc3f7',      # Light blue
                    'secondary': '#81d4fa',    # Lighter blue
                    'accent': '#4dd0e1',       # Light cyan
                    'neutral': '#78909c',      # Light blue gray
                    'error': '#ef5350',        # Light red
                    'warning': '#ffca28',      # Light amber
                    'success': '#4db6ac',      # Light teal
                    'info': '#4fc3f7',         # Light blue
                    'emphasis': '#9575cd',     # Light purple
                    'subtle': '#1c2833',       # Dark blue gray
                    'distinct': '#4dd0e1',     # Light cyan
                    'aether': '#ba68c8',       # Light purple
                    'artifact': '#ffb74d',     # Light amber
                    'sylvan': '#66bb6a',       # Light green
                    'danger': '#ef5350',       # Light red
                    # System colors
                    'background': '#0a0f14',   # Very dark blue
                    'surface': '#1a2332',      # Dark blue
                    'text': '#b3e5fc',         # Light blue
                    'text-secondary': '#4fc3f7',
                },
                'generate_variants': True,
            }
        }
    },
    
    'phoenix': {
        'name': 'phoenix',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#ff6b35',      # Fire orange
                    'secondary': '#f77b71',    # Light red
                    'accent': '#ffc947',       # Gold
                    'neutral': '#a8716a',      # Brown
                    'error': '#c73e1d',        # Deep red
                    'warning': '#ffc947',      # Gold
                    'success': '#5eb319',      # Green
                    'info': '#4a90e2',         # Blue
                    'emphasis': '#b8336a',     # Magenta
                    'subtle': '#fff5e6',       # Light cream
                    'distinct': '#ff9a00',     # Orange
                    'aether': '#c9184a',       # Crimson
                    'artifact': '#d4a574',     # Tan
                    'sylvan': '#7cb342',       # Light green
                    'danger': '#b71c1c',       # Dark red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#fff5e6',      # Cream
                    'text': '#2c1810',         # Dark brown
                    'text-secondary': '#6d4c41',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#ff9575',      # Light orange
                    'secondary': '#ffab91',    # Lighter orange
                    'accent': '#ffd54f',       # Light gold
                    'neutral': '#bcaaa4',      # Light brown
                    'error': '#ff7961',        # Light red
                    'warning': '#ffd54f',      # Light gold
                    'success': '#81c784',      # Light green
                    'info': '#64b5f6',         # Light blue
                    'emphasis': '#f06292',     # Light pink
                    'subtle': '#2c1810',       # Dark brown
                    'distinct': '#ffb74d',     # Light orange
                    'aether': '#e91e63',       # Pink
                    'artifact': '#d7ccc8',     # Light tan
                    'sylvan': '#aed581',       # Light green
                    'danger': '#ef5350',       # Light red
                    # System colors
                    'background': '#0f0a08',   # Very dark brown
                    'surface': '#1f1410',      # Dark brown
                    'text': '#ffe0b2',         # Light orange
                    'text-secondary': '#ffcc80',
                },
                'generate_variants': True,
            }
        }
    },
    
    'shadow': {
        'name': 'shadow',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#000000',      # Black
                    'secondary': '#333333',    # Dark gray
                    'accent': '#666666',       # Gray
                    'neutral': '#999999',      # Light gray
                    'error': '#000000',        # Black
                    'warning': '#333333',      # Dark gray
                    'success': '#666666',      # Gray
                    'info': '#999999',         # Light gray
                    'emphasis': '#000000',     # Black
                    'subtle': '#f5f5f5',       # Very light gray
                    'distinct': '#333333',     # Dark gray
                    'aether': '#666666',       # Gray
                    'artifact': '#999999',     # Light gray
                    'sylvan': '#cccccc',       # Very light gray
                    'danger': '#000000',       # Black
                    # System colors
                    'background': '#ffffff',
                    'surface': '#f5f5f5',
                    'text': '#000000',
                    'text-secondary': '#333333',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#ffffff',      # White
                    'secondary': '#cccccc',    # Light gray
                    'accent': '#999999',       # Gray
                    'neutral': '#666666',      # Dark gray
                    'error': '#ffffff',        # White
                    'warning': '#cccccc',      # Light gray
                    'success': '#999999',      # Gray
                    'info': '#666666',         # Dark gray
                    'emphasis': '#ffffff',     # White
                    'subtle': '#1a1a1a',       # Very dark gray
                    'distinct': '#cccccc',     # Light gray
                    'aether': '#999999',       # Gray
                    'artifact': '#666666',     # Dark gray
                    'sylvan': '#333333',       # Dark gray
                    'danger': '#ffffff',       # White
                    # System colors
                    'background': '#000000',
                    'surface': '#1a1a1a',
                    'text': '#ffffff',
                    'text-secondary': '#cccccc',
                },
                'generate_variants': True,
            }
        }
    },
    
    'enchanted': {
        'name': 'enchanted',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#FF006E',      # Hot pink
                    'secondary': '#FB5607',    # Orange red
                    'accent': '#FFBE0B',       # Yellow
                    'neutral': '#8338EC',      # Purple
                    'error': '#E01E37',        # Red
                    'warning': '#FF9500',      # Orange
                    'success': '#95D600',      # Lime green
                    'info': '#3A86FF',         # Blue
                    'emphasis': '#FF4CC4',     # Pink
                    'subtle': '#FFE5F1',       # Light pink
                    'distinct': '#C77DFF',     # Light purple
                    'aether': '#FF10F0',       # Magenta
                    'artifact': '#FFD700',     # Gold
                    'sylvan': '#7CB518',       # Green
                    'danger': '#DC2F02',       # Deep red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#FFE5F1',      # Light pink
                    'text': '#2D0320',         # Dark purple
                    'text-secondary': '#8338EC',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#FF4D9A',      # Light pink
                    'secondary': '#FF8A65',    # Light orange
                    'accent': '#FFD54F',       # Light yellow
                    'neutral': '#B388FF',      # Light purple
                    'error': '#FF6B7A',        # Light red
                    'warning': '#FFB74D',      # Light orange
                    'success': '#B2FF59',      # Light green
                    'info': '#82B1FF',         # Light blue
                    'emphasis': '#FF80E5',     # Light pink
                    'subtle': '#2D0320',       # Dark purple
                    'distinct': '#E1BEE7',     # Very light purple
                    'aether': '#FF6FFF',       # Light magenta
                    'artifact': '#FFE57F',     # Light gold
                    'sylvan': '#CCFF90',       # Light green
                    'danger': '#FF6E6E',       # Light red
                    # System colors
                    'background': '#0F0014',   # Very dark purple
                    'surface': '#2D0320',      # Dark purple
                    'text': '#FFE5F1',         # Light pink
                    'text-secondary': '#FF80E5',
                },
                'generate_variants': True,
            }
        }
    },
    
    'pastel': {
        'name': 'pastel',
        'modes': {
            'light': {
                'colors': {
                    'primary': '#b19cd9',      # Lavender
                    'secondary': '#ffb6c1',    # Light pink
                    'accent': '#ffd700',       # Gold
                    'neutral': '#e6e6fa',      # Lavender gray
                    'error': '#ff91a4',        # Pink red
                    'warning': '#ffcc99',      # Peach
                    'success': '#90ee90',      # Light green
                    'info': '#87ceeb',         # Sky blue
                    'emphasis': '#dda0dd',     # Plum
                    'subtle': '#faf0e6',       # Linen
                    'distinct': '#98fb98',     # Pale green
                    'aether': '#ff99ff',       # Light magenta
                    'artifact': '#f0e68c',     # Khaki
                    'sylvan': '#98d98e',       # Light sage
                    'danger': '#ffb3ba',       # Light red
                    # System colors
                    'background': '#ffffff',
                    'surface': '#faf0e6',      # Linen
                    'text': '#4a4a4a',         # Dark gray
                    'text-secondary': '#7a7a7a',
                },
                'generate_variants': True,
            },
            'dark': {
                'colors': {
                    'primary': '#d4c5f9',      # Light lavender
                    'secondary': '#ffd4e5',    # Light pink
                    'accent': '#fff59d',       # Light yellow
                    'neutral': '#b39ddb',      # Light purple
                    'error': '#ffcdd2',        # Light red
                    'warning': '#ffe0b2',      # Light peach
                    'success': '#c8e6c9',      # Light green
                    'info': '#b3e5fc',         # Light blue
                    'emphasis': '#f8bbd0',     # Light pink
                    'subtle': '#2e2e3e',       # Dark purple gray
                    'distinct': '#dcedc8',     # Light green
                    'aether': '#ffccff',       # Very light magenta
                    'artifact': '#fff9c4',     # Light yellow
                    'sylvan': '#e6ee9c',       # Light yellow green
                    'danger': '#ffcccc',       # Light pink
                    # System colors
                    'background': '#1a1a2e',   # Dark blue gray
                    'surface': '#2e2e3e',      # Dark gray
                    'text': '#f5f5f5',         # Light gray
                    'text-secondary': '#e0e0e0',
                },
                'generate_variants': True,
            }
        }
    },
}


def get_theme_with_mode(theme_name: str, mode: str = 'light') -> Optional[Dict[str, Any]]:
    """
    Get theme configuration for a specific theme and mode.
    
    Args:
        theme_name: Name of the theme
        mode: 'light' or 'dark'
        
    Returns:
        Theme configuration dictionary
    """
    if theme_name not in THEMES_WITH_MODES:
        return None
    
    theme = THEMES_WITH_MODES[theme_name]
    if mode not in theme.get('modes', {}):
        return None
    
    config = theme['modes'][mode].copy()
    config['name'] = f"{theme_name}-{mode}"
    return config