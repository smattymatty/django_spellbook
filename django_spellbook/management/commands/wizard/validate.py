# django_spellbook/management/commands/wizard/validate.py

import yaml
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import difflib

from django.conf import settings

from django_spellbook.markdown.frontmatter import FrontMatterParser
from django_spellbook.management.commands.spellbook_md_p.discovery import find_markdown_files
from django_spellbook.management.commands.wizard_utils import clear_screen, display_header, show_menu


@dataclass
class ValidationError:
    """Represents a single validation error"""
    field: str
    message: str
    current_value: any = None


class FrontmatterValidator:
    """Validates frontmatter against opinionated defaults."""

    REQUIRED_FIELDS = ['title', 'published', 'author', 'tags']

    def __init__(self, stdout, style_func=None):
        self.stdout = stdout
        self.style = style_func

    def validate_page(self, filepath: Path) -> List[ValidationError]:
        """Return list of validation errors for a single page."""
        errors = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            parser = FrontMatterParser(content, filepath)
            metadata = parser.metadata

            # Validate required fields
            for field in self.REQUIRED_FIELDS:
                if field not in metadata or metadata[field] is None:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Missing: {field}",
                        current_value=None
                    ))
                    continue

                # Validate field types and values
                value = metadata[field]

                if field == 'title':
                    if not isinstance(value, str):
                        errors.append(ValidationError(
                            field=field,
                            message="title must be a string",
                            current_value=value
                        ))
                    elif not value.strip():
                        errors.append(ValidationError(
                            field=field,
                            message="title cannot be empty",
                            current_value=value
                        ))

                elif field == 'published':
                    error = self._validate_date(value, field)
                    if error:
                        errors.append(error)

                elif field == 'author':
                    if not isinstance(value, str):
                        errors.append(ValidationError(
                            field=field,
                            message="author must be a string",
                            current_value=value
                        ))
                    elif not value.strip():
                        errors.append(ValidationError(
                            field=field,
                            message="author cannot be empty",
                            current_value=value
                        ))

                elif field == 'tags':
                    if not isinstance(value, list):
                        errors.append(ValidationError(
                            field=field,
                            message="tags must be a list, got " + type(value).__name__,
                            current_value=value
                        ))
                    elif len(value) == 0:
                        errors.append(ValidationError(
                            field=field,
                            message="tags: must have at least 1 item",
                            current_value=value
                        ))

        except Exception as e:
            errors.append(ValidationError(
                field='file',
                message=f"Error reading file: {str(e)}",
                current_value=None
            ))

        return errors

    def _validate_date(self, value: any, field_name: str) -> Optional[ValidationError]:
        """Validate a date field."""
        # Accept datetime or date objects
        if isinstance(value, (datetime, date)):
            return None

        # String must be YYYY-MM-DD format
        if isinstance(value, str):
            try:
                # Try parsing as YYYY-MM-DD
                datetime.strptime(value.strip(), '%Y-%m-%d')
                return None
            except ValueError:
                return ValidationError(
                    field=field_name,
                    message=f'{field_name}: invalid date format "{value}" (expected YYYY-MM-DD)',
                    current_value=value
                )

        # Invalid type
        return ValidationError(
            field=field_name,
            message=f"{field_name}: must be a date, got {type(value).__name__}",
            current_value=value
        )

    def validate_all(self, source_path: Path) -> Dict[Path, List[ValidationError]]:
        """Validate all markdown files, return errors by file."""
        results = {}

        try:
            markdown_files = find_markdown_files(source_path)
        except Exception as e:
            self._write_error(f"Error finding markdown files: {str(e)}")
            return results

        for dirpath, filename in markdown_files:
            filepath = Path(dirpath) / filename
            errors = self.validate_page(filepath)
            if errors:
                results[filepath] = errors

        return results

    def fix_interactive(self, filepath: Path, errors: List[ValidationError]) -> bool:
        """
        Interactively prompt user to fix each error.
        Returns True if file was modified, False if all skipped.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            parser = FrontMatterParser(content, filepath)
            metadata = parser.metadata.copy()
            modified = False

            self._write_header(f"\n📄 {filepath.name}")

            for error in errors:
                self._write(f"\n   {error.message}")

                if error.field == 'file':
                    continue  # Can't fix file-level errors

                # Prompt for fix
                if error.field in ['title', 'author']:
                    response = input(f"   Enter {error.field} (or 'skip'): ").strip()
                    if response.lower() != 'skip' and response:
                        metadata[error.field] = response
                        modified = True
                    else:
                        self._write("   Skipped")

                elif error.field == 'published':
                    response = input(f"   Enter date (YYYY-MM-DD / 'today' / 'skip'): ").strip()
                    if response.lower() == 'today':
                        metadata[error.field] = datetime.now().strftime('%Y-%m-%d')
                        modified = True
                    elif response.lower() != 'skip' and response:
                        # Validate format
                        try:
                            datetime.strptime(response, '%Y-%m-%d')
                            metadata[error.field] = response
                            modified = True
                        except ValueError:
                            self._write_error(f"   Invalid date format: {response}")
                    else:
                        self._write("   Skipped")

                elif error.field == 'tags':
                    response = input(f"   Enter tags (comma-separated / 'skip'): ").strip()
                    if response.lower() != 'skip' and response:
                        tags = [tag.strip() for tag in response.split(',') if tag.strip()]
                        if tags:
                            metadata[error.field] = tags
                            modified = True
                    else:
                        self._write("   Skipped")

            # Write back if modified
            if modified:
                self._write_file_with_frontmatter(filepath, metadata, parser.raw_content)
                self._write_success(f"\n   ✅ Updated {filepath.name}")

            return modified

        except Exception as e:
            self._write_error(f"   Error fixing file: {str(e)}")
            return False

    def _write_file_with_frontmatter(self, filepath: Path, metadata: Dict, raw_content: str):
        """Write file with updated frontmatter."""
        yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
        new_content = f"---\n{yaml_content}---\n{raw_content}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def _write(self, message: str):
        """Write message to stdout."""
        self.stdout.write(message)

    def _write_success(self, message: str):
        """Write success message."""
        if self.style:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write(message)

    def _write_error(self, message: str):
        """Write error message."""
        if self.style:
            self.stdout.write(self.style.ERROR(message))
        else:
            self.stdout.write(message)

    def _write_warning(self, message: str):
        """Write warning message."""
        if self.style:
            self.stdout.write(self.style.WARNING(message))
        else:
            self.stdout.write(message)

    def _write_header(self, message: str):
        """Write header message."""
        if self.style:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write(message)


class DeadLinkFinder:
    """Finds broken internal links in processed content."""

    def __init__(self, stdout, style_func=None):
        self.stdout = stdout
        self.style = style_func
        self.known_urls: Set[str] = set()
        self.known_anchors: Dict[str, Set[str]] = {}

    def find_dead_links(self, source_paths: List[Path]) -> Dict[Path, List[str]]:
        """
        Scan all markdown files for dead links.
        Returns dict of {filepath: [error_messages]}
        """
        # For now, return a placeholder message since this requires HTML parsing
        # which depends on processed files
        self._write_warning("\n🔗 Dead link detection coming soon!")
        self._write("\nThis feature requires HTML parsing of processed files.")
        self._write("It will be implemented in a future update.\n")
        return {}

    def _write(self, message: str):
        """Write message to stdout."""
        self.stdout.write(message)

    def _write_warning(self, message: str):
        """Write warning message."""
        if self.style:
            self.stdout.write(self.style.WARNING(message))
        else:
            self.stdout.write(message)


# Menu handler functions

def handle_validate_menu(command_instance):
    """Display validate submenu and handle selections."""
    while True:
        choice = show_menu(
            '🔍 Validate',
            [
                ('1', 'Validate frontmatter (spellbook_validate)'),
                ('2', 'Find dead links'),
            ],
            allow_back=True,
            style_func=command_instance.style
        )

        if choice == '0':
            clear_screen()
            return
        elif choice == '1':
            handle_frontmatter_validation(command_instance)
        elif choice == '2':
            handle_dead_links(command_instance)


def handle_frontmatter_validation(command_instance):
    """Handle frontmatter validation."""
    clear_screen()
    display_header('🔍 Validating frontmatter...', command_instance.style)

    # Get source paths from settings
    try:
        from django_spellbook.management.commands.command_utils import validate_spellbook_settings
        md_file_paths, _, _, _, _ = validate_spellbook_settings()
    except Exception as e:
        command_instance.stdout.write(command_instance.style.ERROR(f"\n  Error: {str(e)}\n"))
        input("\n  Press Enter to continue...")
        clear_screen()
        return

    # Create validator
    validator = FrontmatterValidator(command_instance.stdout, command_instance.style)

    # Validate all files across all source paths
    all_errors = {}
    total_files = 0

    for source_path in md_file_paths:
        errors = validator.validate_all(Path(source_path))
        all_errors.update(errors)

        # Count total files
        try:
            markdown_files = find_markdown_files(source_path)
            total_files += len(markdown_files)
        except:
            pass

    # Display results
    if all_errors:
        command_instance.stdout.write(f"\n")
        for filepath, errors in all_errors.items():
            command_instance.stdout.write(command_instance.style.ERROR(f"❌ {filepath}"))
            for error in errors:
                command_instance.stdout.write(f"   • {error.message}")
            command_instance.stdout.write("\n")

        command_instance.stdout.write("─" * 40)
        command_instance.stdout.write(command_instance.style.WARNING(f"\n⚠️  {len(all_errors)} pages with issues"))
        command_instance.stdout.write(command_instance.style.SUCCESS(f"\n✅ {total_files - len(all_errors)} pages valid\n"))

        # Ask if user wants to fix interactively
        fix_response = input("\nRun interactive fix? (y/n): ").strip().lower()
        if fix_response == 'y':
            fixed_count = 0
            skipped_count = 0

            for filepath, errors in all_errors.items():
                if validator.fix_interactive(filepath, errors):
                    fixed_count += 1
                else:
                    skipped_count += 1

            command_instance.stdout.write("\n" + "─" * 40)
            if fixed_count > 0:
                command_instance.stdout.write(command_instance.style.SUCCESS(f"\n✅ Fixed {fixed_count} pages"))
            if skipped_count > 0:
                command_instance.stdout.write(command_instance.style.WARNING(f"\n⏭️  Skipped {skipped_count} pages"))
    else:
        command_instance.stdout.write(command_instance.style.SUCCESS(f"\n✅ All {total_files} pages valid!\n"))

    input("\n  Press Enter to continue...")
    clear_screen()


def handle_dead_links(command_instance):
    """Handle dead link detection."""
    clear_screen()
    display_header('🔗 Scanning for dead links...', command_instance.style)

    # Get source paths from settings
    try:
        from django_spellbook.management.commands.command_utils import validate_spellbook_settings
        md_file_paths, _, _, _, _ = validate_spellbook_settings()
    except Exception as e:
        command_instance.stdout.write(command_instance.style.ERROR(f"\n  Error: {str(e)}\n"))
        input("\n  Press Enter to continue...")
        clear_screen()
        return

    # Create dead link finder
    finder = DeadLinkFinder(command_instance.stdout, command_instance.style)

    # Find dead links
    source_paths = [Path(p) for p in md_file_paths]
    dead_links = finder.find_dead_links(source_paths)

    # Display results (when implemented)

    input("\n  Press Enter to continue...")
    clear_screen()
