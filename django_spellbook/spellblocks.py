# myapp/spellblocks.py
from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry
from typing import Optional

import logging
logger = logging.getLogger(__name__)

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
    
@SpellBlockRegistry.register()
class ProgressBarBlock(BasicSpellBlock):
    """
    SpellBlock for rendering a progress bar.
    """
    name = "progress"
    template = "django_spellbook/blocks/progress.html"
    
    def _to_bool(self, value, default=False):
        """Helper to convert common string values to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 't', 'y', 'yes']
        return default # pragma: no cover

    def get_context(self):
        context = super().get_context()
        
        # --- 1. Validation & Type Conversion ---
        raw_value = 0.0
        raw_max_value = 100.0
        try:
            # Convert value upfront
            raw_value = float(self.kwargs.get("value", 0)) 
        except (ValueError, TypeError) as e:
            logger.warning(f"ProgressBarBlock: Invalid 'value' parameter: {self.kwargs.get('value')}. Defaulting to 0. Error: {e}")
            raw_value = 0.0 
        
        try:
             # Convert max_value upfront
            raw_max_value = float(self.kwargs.get("max_value", 100))
            if raw_max_value <= 0: # Max must be positive
               logger.warning(f"ProgressBarBlock: Invalid 'max_value' parameter: {raw_max_value}. Must be > 0. Defaulting to 100.")
               raw_max_value = 100.0
        except (ValueError, TypeError) as e:
            logger.warning(f"ProgressBarBlock: Invalid 'max_value' parameter: {self.kwargs.get('max_value')}. Defaulting to 100. Error: {e}")
            raw_max_value = 100.0

        context['raw_value'] = raw_value
        context['raw_max_value'] = raw_max_value

        # Convert boolean parameters
        context['striped'] = self._to_bool(self.kwargs.get('striped', False))
        context['animated'] = self._to_bool(self.kwargs.get('animated', False))
        context['rounded'] = self._to_bool(self.kwargs.get('rounded', True))

        # Original label and default show_percentage logic
        original_label = self.kwargs.get("label", None)
        default_show_percentage = original_label is None # Default to True only if no label is provided
        show_percentage = self._to_bool(self.kwargs.get("show_percentage", default_show_percentage))
        
        context['label'] = original_label # Store original for reference if needed
        context['show_percentage'] = show_percentage

        # Standard string/optional parameters
        context["color"] = self.kwargs.get("color", "primary")
        context["bg_color"] = self.kwargs.get("bg_color", "white-50")
        context["content_color"] = self.kwargs.get("content_color", "black")
        context["content_bg_color"] = self.kwargs.get("content_bg_color", "white")
        context["height"] = self.kwargs.get("height", "md")
        context["class"] = self.kwargs.get("class", None) 
        context["id"] = self.kwargs.get("id", None) 
        context["content_class"] = self.kwargs.get("content_class", None)

        # --- 2. Percentage Calculation ---
        percentage = 0.0
        # Value clamping before calculation ensures percentage is 0-100
        clamped_value = max(0.0, min(raw_value, raw_max_value)) 
        percentage = round((clamped_value / raw_max_value) * 100, 2)
        
        context['calculated_percentage'] = percentage

        # --- 3. Label Interpolation ---
        processed_label = ""
        if original_label:
            processed_label = str(original_label) # Ensure it's a string
            processed_label = processed_label.replace("{{value}}", str(raw_value)) 
            processed_label = processed_label.replace("{{max_value}}", str(raw_max_value))
            processed_label = processed_label.replace("{{percentage}}", str(percentage)) # Use calculated percentage here
        context['processed_label'] = processed_label 
        
        return context
    
