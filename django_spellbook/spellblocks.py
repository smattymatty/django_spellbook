# myapp/spellblocks.py
from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry
from typing import Optional


@SpellBlockRegistry.register()
class AlertBlock(BasicSpellBlock):
    name = 'alert'
    template = 'django_spellbook/blocks/alert.html'

    # Define valid alert types
    VALID_TYPES = {'info', 'warning', 'success',
                   'danger', 'primary', 'secondary'}

    def get_context(self):
        context = super().get_context()

        # Validate and set alert type
        alert_type = self.kwargs.get('type', 'info').lower()
        if alert_type not in self.VALID_TYPES:
            print(f"Warning: Invalid alert type '{alert_type}'. Using 'info' instead. "
                  f"Valid types are: {', '.join(sorted(self.VALID_TYPES))}")
            alert_type = 'info'

        context['type'] = alert_type
        return context


@SpellBlockRegistry.register()
class CardBlock(BasicSpellBlock):
    name = 'card'
    template = 'django_spellbook/blocks/card.html'

    def get_context(self):
        context = super().get_context()

        # Optional title and footer
        context['title'] = self.kwargs.get('title')
        context['footer'] = self.kwargs.get('footer')

        # Additional styling classes
        context['class'] = self.kwargs.get('class', '')

        return context

@SpellBlockRegistry.register()
class QuoteBlock(BasicSpellBlock):
    name = 'quote'
    template = 'django_spellbook/blocks/quote.html'

    def get_context(self):
        context = super().get_context()
        context['author'] = self.kwargs.get('author', '')
        context['source'] = self.kwargs.get('source', '')
        context['image'] = self.kwargs.get('image', '')
        
        # Additional styling classes
        context['class'] = self.kwargs.get('class', '')
        return context
    
    
@SpellBlockRegistry.register()
class PracticeBlock(BasicSpellBlock):
    name = 'practice'
    template = 'django_spellbook/blocks/practice.html'

    def get_context(self):
        context = super().get_context()
        context['difficulty'] = self.kwargs.get('difficulty', 'Moderate')
        context['timeframe'] = self.kwargs.get('timeframe', 'Varies')
        context['impact'] = self.kwargs.get('impact', 'Medium')
        context['focus'] = self.kwargs.get('focus', 'General')
        
        # Additional styling classes
        context['class'] = self.kwargs.get('class', '')
        return context
    
    
@SpellBlockRegistry.register()
class AccordionBlock(BasicSpellBlock):
    name = 'accordion'
    template = 'django_spellbook/blocks/accordion.html'

    def get_context(self):
        context = super().get_context()
        # Add your custom context here via self.kwargs.get('name', '')
        context['title'] = self.kwargs.get('title', '')
        context['open'] = self.kwargs.get('open', False)
        return context

# --- Dummy SpellBlocks for Testing ---

@SpellBlockRegistry.register()
class SimpleTestBlock(BasicSpellBlock):
    name = "simple"
    template = "django_spellbook/blocks/test_blocks/simple_block.html" # Will look in tests/templates/test_blocks/simple_block.html

    def __init__(self, content=None, reporter=None, spellbook_parser=None, **kwargs):
        super().__init__(content=content, reporter=reporter, spellbook_parser=spellbook_parser, **kwargs)
        self.name = SimpleTestBlock.name # Ensure name is set on instance
        self.template = SimpleTestBlock.template # Ensure template is set on instance

@SpellBlockRegistry.register()
class SelfClosingTestBlock(BasicSpellBlock):
    name = "selfclosing"
    template = "django_spellbook/blocks/test_blocks/self_closing_block.html"

    def __init__(self, content=None, reporter=None, spellbook_parser=None, **kwargs):
        super().__init__(content=content, reporter=reporter, spellbook_parser=spellbook_parser, **kwargs)
        self.name = SelfClosingTestBlock.name
        self.template = SelfClosingTestBlock.template

@SpellBlockRegistry.register()
class ArgsTestBlock(BasicSpellBlock):
    name = "argstest"
    template = "django_spellbook/blocks/test_blocks/args_test_block.html"

    def __init__(self, content=None, reporter=None, spellbook_parser=None, **kwargs):
        super().__init__(content=content, reporter=reporter, spellbook_parser=spellbook_parser, **kwargs)
        # BasicSpellBlock.__init__ should handle setting self.name and self.template
        # from class attributes if they are not already instance attributes.

    def get_context(self) -> dict:
        super().get_context() # Call parent's get_context to ensure self.kwargs is set
        # self.kwargs contains the arguments passed to the block instance (parsed from the tag)
        # self.content is the raw content string from between the block tags

        # BasicSpellBlock's process_content() turns self.content (Markdown) into HTML
        processed_content_html = self.process_content()

        context = {
            'content': processed_content_html,
            # Provide the parsed arguments, sorted by key for predictable template output
            'parsed_args_sorted': sorted(self.kwargs.items())
        }
        return context