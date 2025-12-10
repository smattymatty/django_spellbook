# django_spellbook/management/commands/spellbook_wizard.py

import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

from django_spellbook.management.commands.wizard_utils import (
    show_menu,
    clear_screen,
    display_header
)
from django_spellbook.management.commands.wizard.validate import handle_validate_menu

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Interactive wizard for Django Spellbook tasks'

    def handle(self, *args, **options):
        """Launch the interactive wizard."""
        clear_screen()
        self.main_menu()

    def main_menu(self):
        """Display main menu with top-level categories."""
        while True:
            choice = show_menu(
                'Spellbook Wizard',
                [
                    ('1', 'Batch process'),
                    ('2', 'Validate'),
                ],
                allow_back=False,
                style_func=self.style
            )

            if choice == '0':
                self.stdout.write(self.style.SUCCESS("\n  Goodbye!\n"))
                break
            elif choice == '1':
                clear_screen()
                self.batch_process_menu()
            elif choice == '2':
                clear_screen()
                handle_validate_menu(self)

    def batch_process_menu(self):
        """Display batch processing submenu."""
        while True:
            choice = show_menu(
                'Batch Process',
                [
                    ('1', 'Process markdown (spellbook_md)'),
                ],
                allow_back=True,
                style_func=self.style
            )

            if choice == '0':
                clear_screen()
                return
            elif choice == '1':
                self.run_spellbook_md()

    def run_spellbook_md(self):
        """Execute the spellbook_md command."""
        clear_screen()
        display_header('Running spellbook_md...', self.style)

        try:
            # Call the spellbook_md command
            call_command('spellbook_md')

            self.stdout.write(self.style.SUCCESS("\n  spellbook_md completed successfully!\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n  Error running spellbook_md: {str(e)}\n"))
            logger.error(f"Wizard: spellbook_md failed: {str(e)}", exc_info=True)

        input("\n  Press Enter to continue...")
        clear_screen()
