# django_spellbook/management/commands/spellbook_validate.py

import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from django_spellbook.management.commands.command_utils import validate_spellbook_settings
from django_spellbook.management.commands.wizard.validate import FrontmatterValidator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate frontmatter in markdown files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Interactively fix frontmatter issues'
        )
        parser.add_argument(
            '--source-path',
            type=str,
            help='Override source path from settings (useful for testing specific directories)'
        )

    def handle(self, *args, **options):
        """Validate frontmatter in markdown files."""
        fix_mode = options.get('fix', False)
        source_path_override = options.get('source_path')

        # Get source paths from settings or override
        if source_path_override:
            md_file_paths = [Path(source_path_override)]
            self.stdout.write(self.style.SUCCESS(f"\nUsing source path: {source_path_override}\n"))
        else:
            try:
                md_file_paths, _, _, _, _ = validate_spellbook_settings()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\nError: {str(e)}\n"))
                self.stdout.write(
                    "Please check your Django settings.py file and ensure "
                    "SPELLBOOK_MD_PATH and SPELLBOOK_MD_APP are correctly configured.\n"
                )
                return

        # Create validator
        validator = FrontmatterValidator(self.stdout, self.style)

        # Validate all files across all source paths
        all_errors = {}
        total_files = 0

        for source_path in md_file_paths:
            self.stdout.write(f"Validating: {source_path}\n")

            try:
                from django_spellbook.management.commands.spellbook_md_p.discovery import find_markdown_files
                markdown_files = find_markdown_files(source_path)
                total_files += len(markdown_files)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Warning: Could not scan {source_path}: {str(e)}\n"))
                continue

            errors = validator.validate_all(Path(source_path))
            all_errors.update(errors)

        # Display results
        self.stdout.write("\n" + "─" * 60 + "\n")

        if all_errors:
            self.stdout.write(self.style.WARNING(f"\n🔍 Validation Results\n"))
            self.stdout.write("\n")

            for filepath, errors in all_errors.items():
                self.stdout.write(self.style.ERROR(f"❌ {filepath}"))
                for error in errors:
                    self.stdout.write(f"   • {error.message}")
                self.stdout.write("\n")

            self.stdout.write("─" * 60)
            self.stdout.write(self.style.WARNING(f"\n⚠️  {len(all_errors)} pages with issues"))
            self.stdout.write(self.style.SUCCESS(f"\n✅ {total_files - len(all_errors)} pages valid\n"))

            if fix_mode:
                # Interactive fix mode
                self.stdout.write("\n" + "─" * 60 + "\n")
                self.stdout.write(self.style.SUCCESS("🔧 Interactive Fix Mode\n"))

                fixed_count = 0
                skipped_count = 0

                for filepath, errors in all_errors.items():
                    if validator.fix_interactive(filepath, errors):
                        fixed_count += 1
                    else:
                        skipped_count += 1

                self.stdout.write("\n" + "─" * 60)
                if fixed_count > 0:
                    self.stdout.write(self.style.SUCCESS(f"\n✅ Fixed {fixed_count} pages"))
                if skipped_count > 0:
                    self.stdout.write(self.style.WARNING(f"\n⏭️  Skipped {skipped_count} pages"))
                self.stdout.write("\n")
            else:
                # Audit mode - suggest using --fix
                self.stdout.write(f"\nRun with --fix to interactively repair issues:\n")
                self.stdout.write(f"  python manage.py spellbook_validate --fix\n\n")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ All {total_files} pages valid!\n\n"))
