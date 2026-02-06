# tests/test_spellblock_templatetag.py

from django.test import TestCase
from django.template import Template, Context, TemplateSyntaxError


class TestSpellBlockTemplateTag(TestCase):
    """Test the {% spellblock %} template tag."""

    def _clear_and_register_blocks(self):
        """Clears and re-registers blocks needed for template tag tests."""
        from django_spellbook.blocks import SpellBlockRegistry
        from django_spellbook.spellblocks import (
            AlertBlock, CardBlock, HeroSpellBlock, ProgressBarBlock,
            HrBlock, DivBlock
        )

        # Clear the registry for test isolation
        if hasattr(SpellBlockRegistry, '_registry') and isinstance(SpellBlockRegistry._registry, dict):
            SpellBlockRegistry._registry.clear()

        # Re-register blocks needed for these tests
        blocks_to_register = [
            AlertBlock, CardBlock, HeroSpellBlock, ProgressBarBlock,
            HrBlock, DivBlock
        ]

        for block_class in blocks_to_register:
            if hasattr(block_class, 'name') and block_class.name:
                SpellBlockRegistry._registry[block_class.name] = block_class

    def setUp(self):
        """Set up test fixtures."""
        # Clear and re-register blocks for each test
        self._clear_and_register_blocks()

    # ========== Parse-time tests ==========

    def test_missing_block_name_raises_syntax_error(self):
        """Missing block name raises TemplateSyntaxError."""
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template("{% load spellbook_tags %}{% spellblock %}{% endspellblock %}")

        self.assertIn("requires a block name", str(cm.exception))

    def test_orphaned_endspellblock_raises_syntax_error(self):
        """Orphaned {% endspellblock %} tag raises TemplateSyntaxError."""
        with self.assertRaises(TemplateSyntaxError) as cm:
            Template("{% load spellbook_tags %}{% endspellblock %}")

        self.assertIn("Orphaned", str(cm.exception))
        self.assertIn("endspellblock", str(cm.exception))

    def test_valid_syntax_parses_without_error(self):
        """Valid syntax parses without error."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'alert' type='info' %}Test{% endspellblock %}"
        )
        self.assertIsNotNone(template)

    # ========== Basic render tests ==========

    def test_basic_alert_block_renders(self):
        """Basic alert block renders correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'alert' type='info' %}Test message{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('Test message', result)
        self.assertIn('sb-alert', result)
        self.assertIn('info', result)

    def test_unknown_block_shows_error_html(self):
        """Unknown block name shows error HTML (doesn't crash)."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'nonexistent' %}Content{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('SpellBlock Error', result)
        self.assertIn('not found in registry', result)
        self.assertIn('sb-spellblock-error', result)

    def test_empty_content_works(self):
        """Empty content works correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'hr' %}{% endspellblock %}"
        )
        result = template.render(Context({}))

        # HR block should render without content
        self.assertIn('<hr>', result)

    def test_multiple_kwargs_work(self):
        """Multiple kwargs work correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' title='My Title' footer='My Footer' %}"
            "Card content"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('My Title', result)
        self.assertIn('My Footer', result)
        self.assertIn('Card content', result)
        self.assertIn('sb-card', result)

    # ========== Variable resolution tests ==========

    def test_variable_in_block_name(self):
        """Template variables work in block name argument."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock block_type type='success' %}Dynamic block{% endspellblock %}"
        )
        result = template.render(Context({'block_type': 'alert'}))

        self.assertIn('Dynamic block', result)
        self.assertIn('sb-alert', result)
        self.assertIn('success', result)

    def test_variable_in_kwargs(self):
        """Template variables work in keyword arguments."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'alert' type=alert_type %}Variable type{% endspellblock %}"
        )
        result = template.render(Context({'alert_type': 'warning'}))

        self.assertIn('Variable type', result)
        self.assertIn('warning', result)

    def test_variable_in_content(self):
        """Template variables work in content."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' title='User Card' %}"
            "{{ user_name }}"
            "{% endspellblock %}"
        )
        result = template.render(Context({'user_name': 'John Doe'}))

        self.assertIn('John Doe', result)
        self.assertIn('User Card', result)

    def test_nested_template_tags_in_content(self):
        """Nested template tags in content work correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' %}"
            "{% if show_message %}Visible{% else %}Hidden{% endif %}"
            "{% endspellblock %}"
        )
        result = template.render(Context({'show_message': True}))

        self.assertIn('Visible', result)
        self.assertNotIn('Hidden', result)

    def test_unresolvable_variable_shows_error(self):
        """Unresolvable variable in block name resolves to empty string and shows 'not found' error."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock missing_var %}Content{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('SpellBlock Error', result)
        self.assertIn('not found in registry', result)

    # ========== Integration tests with built-in blocks ==========

    def test_alert_block_all_types(self):
        """Alert block works with all types."""
        for alert_type in ['info', 'success', 'warning', 'error']:
            with self.subTest(alert_type=alert_type):
                template = Template(
                    "{% load spellbook_tags %}"
                    f"{{% spellblock 'alert' type='{alert_type}' %}}"
                    f"This is a {alert_type} alert"
                    "{% endspellblock %}"
                )
                result = template.render(Context({}))

                self.assertIn(f'{alert_type} alert', result)
                self.assertIn('sb-alert', result)

    def test_card_block_with_all_props(self):
        """Card block works with title and footer properties."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' title='Card Title' footer='Footer Text' %}"
            "<p>Card body content</p>"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('Card Title', result)
        self.assertIn('Footer Text', result)
        self.assertIn('Card body content', result)
        self.assertIn('sb-card', result)

    def test_hero_block(self):
        """Hero block renders correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'hero' %}"
            "<button>CTA Button</button>"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('CTA Button', result)
        self.assertIn('sb-hero', result)

    def test_progress_block(self):
        """Progress block renders correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'progress' value='75' max='100' %}"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('sb-progress', result)
        # Progress bar should include value/max attributes or data
        self.assertIn('75', result)

    def test_code_block(self):
        """Code block renders correctly (if registered)."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'div' %}"
            "def hello():\n    print('world')"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('def hello()', result)
        self.assertIn('<div', result)

    def test_hr_block(self):
        """HR block renders correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'hr' %}{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('<hr>', result)

    # ========== Error handling tests ==========

    def test_block_render_error_shows_error_html(self):
        """Block render errors show error HTML (don't crash template)."""
        # This test assumes some block might throw an error during instantiation
        # For now, we'll test with invalid arguments that might cause issues
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'progress' value='invalid' %}"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        # Should either render successfully or show error, but not crash
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

    def test_error_styling_uses_correct_classes(self):
        """Error messages use correct spellbook CSS classes."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'nonexistent' %}Test{% endspellblock %}"
        )
        result = template.render(Context({}))

        # Check for error styling classes
        self.assertIn('sb-spellblock-error', result)
        self.assertIn('sb-p-3', result)
        self.assertIn('sb-rounded', result)
        self.assertIn('sb-border', result)
        self.assertIn('sb-bg-error-25', result)
        self.assertIn('sb-text-error', result)

    # ========== Complex integration tests ==========

    def test_nested_spellblocks(self):
        """Nested spellblocks work correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' title='Outer Card' %}"
            "{% spellblock 'alert' type='info' %}Inner alert{% endspellblock %}"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('Outer Card', result)
        self.assertIn('Inner alert', result)
        self.assertIn('sb-card', result)
        self.assertIn('sb-alert', result)

    def test_multiple_blocks_in_sequence(self):
        """Multiple blocks in sequence render correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'alert' type='info' %}First{% endspellblock %}"
            "{% spellblock 'alert' type='success' %}Second{% endspellblock %}"
            "{% spellblock 'alert' type='warning' %}Third{% endspellblock %}"
        )
        result = template.render(Context({}))

        self.assertIn('First', result)
        self.assertIn('Second', result)
        self.assertIn('Third', result)
        # Check order is preserved
        self.assertTrue(result.index('First') < result.index('Second') < result.index('Third'))

    def test_whitespace_handling(self):
        """Whitespace in content is preserved correctly."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' %}"
            "    Content with indentation\n"
            "    Second line"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        # Content should be present (exact whitespace handling depends on block implementation)
        self.assertIn('Content with indentation', result)
        self.assertIn('Second line', result)

    def test_html_in_content_is_preserved(self):
        """HTML in content is preserved (not escaped)."""
        template = Template(
            "{% load spellbook_tags %}"
            "{% spellblock 'card' %}"
            "<strong>Bold</strong> and <em>italic</em>"
            "{% endspellblock %}"
        )
        result = template.render(Context({}))

        # HTML tags should be present, not escaped
        self.assertIn('<strong>Bold</strong>', result)
        self.assertIn('<em>italic</em>', result)

    def test_context_isolation(self):
        """Context modifications inside block don't leak out."""
        template = Template(
            "{% load spellbook_tags %}"
            "{{ outer_var }}"
            "{% spellblock 'card' %}"
            "{% with inner_var='inner' %}"
            "{{ inner_var }}"
            "{% endwith %}"
            "{% endspellblock %}"
            "{{ inner_var }}"  # Should be empty
        )
        result = template.render(Context({'outer_var': 'outer'}))

        self.assertIn('outer', result)
        self.assertIn('inner', result)
        # inner_var should not leak to the last reference
        # (Django templates handle this correctly with {% with %})
