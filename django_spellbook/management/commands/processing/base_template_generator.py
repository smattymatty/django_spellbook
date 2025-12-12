from pathlib import Path
from typing import Optional


class SpellbookBaseGenerator:
    """Generates or removes spellbook_base.html based on EXTEND_FROM setting."""

    # Path to the skeleton template relative to this file
    SKELETON_PATH = (
        Path(__file__).parent.parent.parent.parent
        / 'templates' / 'django_spellbook' / 'generated'
        / 'spellbook_base_skeleton.html'
    )

    def __init__(self, content_app: str, template_dir: Path, extend_from: Optional[str]):
        """
        Initialize the generator.

        Args:
            content_app: Name of the content app
            template_dir: Path to the app's template directory
            extend_from: User's base template path to extend from (or None)
        """
        self.content_app = content_app
        self.template_dir = template_dir
        self.extend_from = extend_from
        self.output_path = template_dir / 'spellbook_base.html'

    def process(self) -> Optional[str]:
        """
        Generate or cleanup spellbook_base.html based on extend_from setting.

        Returns:
            str: Relative path to generated base template (e.g., 'my_app/spellbook_base.html'),
                 or None if using default (cleanup occurred or no generation needed)
        """
        if self.extend_from:
            return self._generate()
        else:
            return self._cleanup()

    def _generate(self) -> str:
        """
        Generate spellbook_base.html from skeleton template.

        Returns:
            str: Relative path to the generated template
        """
        # Read skeleton template
        skeleton = self.SKELETON_PATH.read_text()

        # Replace placeholder with actual template path
        content = skeleton.replace('__EXTEND_FROM__', self.extend_from)

        # Ensure directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write generated file
        self.output_path.write_text(content)

        # Return relative path for template inheritance
        return f'{self.content_app}/spellbook_base.html'

    def _cleanup(self) -> None:
        """
        Remove spellbook_base.html if it exists.

        Returns:
            None
        """
        if self.output_path.exists():
            self.output_path.unlink()
        return None
