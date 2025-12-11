# django_spellbook/management/commands/wizard_utils.py

import os
import sys
from typing import List, Tuple, Optional


def clear_screen():
    """Clear the terminal screen (optional, for cleaner UX)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu(
    title: str,
    options: List[Tuple[str, str]],
    allow_back: bool = True,
    style_func=None
) -> str:
    """
    Display a menu and get user selection.

    Args:
        title: Menu title to display at the top
        options: List of (key, label) tuples, e.g., [('1', 'Process markdown')]
        allow_back: If True, show [0] Back/Exit option
        style_func: Optional Django style function for colored output

    Returns:
        User's selection as a string (e.g., '1', '2', '0')

    Example:
        choice = show_menu(
            'Main Menu',
            [('1', 'Batch process'), ('2', 'Validate')],
            allow_back=False
        )
    """
    while True:
        # Display menu header
        print()
        if style_func:
            print(style_func.SUCCESS(f"  {title}"))
        else:
            print(f"  {title}")
        print()

        # Display options
        valid_choices = []
        for key, label in options:
            print(f"  [{key}] {label}")
            valid_choices.append(key)

        # Display back/exit option
        if allow_back:
            print()
            print("  [0] ← Back")
            valid_choices.append('0')
        else:
            print()
            print("  [0] Exit")
            valid_choices.append('0')

        print()

        # Get user input
        try:
            choice = input("> ").strip()

            if choice in valid_choices:
                return choice
            else:
                if style_func:
                    print(style_func.ERROR(f"\n  Invalid selection: '{choice}'. Please try again."))
                else:
                    print(f"\n  Invalid selection: '{choice}'. Please try again.")
                input("\n  Press Enter to continue...")
                clear_screen()

        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C or Ctrl+D gracefully
            print("\n")
            if style_func:
                print(style_func.WARNING("  Exiting wizard..."))
            else:
                print("  Exiting wizard...")
            return '0'


def display_header(text: str, style_func=None):
    """
    Display a formatted header with a separator line.

    Args:
        text: Header text
        style_func: Optional Django style function
    """
    print()
    if style_func:
        print(style_func.SUCCESS(f"  {text}"))
    else:
        print(f"  {text}")
    print("  " + "-" * len(text))
    print()


def confirm_action(prompt: str, default: bool = True, style_func=None) -> bool:
    """
    Ask user for yes/no confirmation.

    Args:
        prompt: Question to ask user
        default: Default value if user just presses Enter
        style_func: Optional Django style function

    Returns:
        True if user confirms, False otherwise
    """
    if default:
        options = "[Y/n]"
    else:
        options = "[y/N]"

    while True:
        if style_func:
            response = input(f"  {style_func.WARNING(prompt)} {options}: ").strip().lower()
        else:
            response = input(f"  {prompt} {options}: ").strip().lower()

        if response == '':
            return default
        elif response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            if style_func:
                print(style_func.ERROR("  Please answer 'y' or 'n'."))
            else:
                print("  Please answer 'y' or 'n'.")
