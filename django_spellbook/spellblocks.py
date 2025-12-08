# django_spellbook/spellblocks.py
import re

from django_spellbook.blocks import BasicSpellBlock, SpellBlockRegistry
from typing import Optional, Dict, Any

import logging
logger = logging.getLogger(__name__)


# ============================================================================
# HTML Element Base Class
# ============================================================================

class HTMLElementBlock(BasicSpellBlock):
    """
    Base class for HTML element SpellBlocks.

    This class renders arbitrary HTML elements with dynamic attributes,
    supporting both void elements (like <hr>) and content-wrapping elements (like <div>).

    Subclasses should define:
        - name: The SpellBlock name (e.g., 'div', 'section')
        - tag_name: The HTML tag name (e.g., 'div', 'section')
        - is_void: True for void elements that don't have closing tags

    Example usage in markdown:
        {~ div .my-class #my-id hx-get="/api" ~}
        Content here
        {~~}

        {~ hr .divider ~}{~~}  # Void element (content ignored)
    """
    tag_name: str = None  # Must be set by subclass
    is_void: bool = False  # True for <hr>, <br>, etc.

    def get_context(self) -> Dict[str, Any]:
        """
        Build context for HTML element rendering.

        Returns:
            Dictionary with:
            - tag_name: HTML tag name
            - is_void: Whether element is void
            - attributes: All kwargs as HTML attributes
            - content: Processed markdown content (empty for void elements)
        """
        if not self.tag_name:
            raise ValueError(
                f"{self.__class__.__name__} must define 'tag_name' class attribute"
            )

        # Validate void elements don't have content
        if self.is_void and self.content and self.content.strip():
            logger.error(
                f"Void element '{self.tag_name}' cannot have content. "
                f"Content will be ignored: {self.content[:50]}..."
            )
            if self.reporter:
                self.reporter.error(
                    f"Void element '{self.tag_name}' cannot have content (content ignored)"
                )

        context = {
            'tag_name': self.tag_name,
            'is_void': self.is_void,
            'attributes': self.kwargs,  # Pass all kwargs as attributes
            'content': '' if self.is_void else self.process_content(),
        }

        return context

    def render(self) -> str:
        """
        Render the HTML element using the generic template.

        Returns:
            Rendered HTML string
        """
        if not self.template:
            # Use default template for HTML elements
            self.template = 'django_spellbook/blocks/html_element.html'

        return super().render()


# ============================================================================
# HTML Element SpellBlocks
# ============================================================================

# Block-level elements
@SpellBlockRegistry.register()
class DivBlock(HTMLElementBlock):
    """Renders a <div> element with dynamic attributes."""
    name = 'div'
    tag_name = 'div'
    is_void = False


@SpellBlockRegistry.register()
class SectionBlock(HTMLElementBlock):
    """Renders a <section> element with dynamic attributes."""
    name = 'section'
    tag_name = 'section'
    is_void = False


@SpellBlockRegistry.register()
class ArticleBlock(HTMLElementBlock):
    """Renders an <article> element with dynamic attributes."""
    name = 'article'
    tag_name = 'article'
    is_void = False


@SpellBlockRegistry.register()
class AsideBlock(HTMLElementBlock):
    """Renders an <aside> element with dynamic attributes."""
    name = 'aside'
    tag_name = 'aside'
    is_void = False


@SpellBlockRegistry.register()
class HeaderBlock(HTMLElementBlock):
    """Renders a <header> element with dynamic attributes."""
    name = 'header'
    tag_name = 'header'
    is_void = False


@SpellBlockRegistry.register()
class FooterBlock(HTMLElementBlock):
    """Renders a <footer> element with dynamic attributes."""
    name = 'footer'
    tag_name = 'footer'
    is_void = False


@SpellBlockRegistry.register()
class NavBlock(HTMLElementBlock):
    """Renders a <nav> element with dynamic attributes."""
    name = 'nav'
    tag_name = 'nav'
    is_void = False


@SpellBlockRegistry.register()
class MainBlock(HTMLElementBlock):
    """Renders a <main> element with dynamic attributes."""
    name = 'main'
    tag_name = 'main'
    is_void = False


# Void elements
@SpellBlockRegistry.register()
class HrBlock(HTMLElementBlock):
    """Renders a <hr> void element with dynamic attributes."""
    name = 'hr'
    tag_name = 'hr'
    is_void = True


@SpellBlockRegistry.register()
class BrBlock(HTMLElementBlock):
    """Renders a <br> void element with dynamic attributes."""
    name = 'br'
    tag_name = 'br'
    is_void = True


# ============================================================================
# Existing SpellBlocks
# ============================================================================

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
    
@SpellBlockRegistry.register()
class HeroSpellBlock(BasicSpellBlock):
    name = "hero"
    template = "django_spellbook/blocks/hero.html" # Main template for the hero block

    # Define MVP parameters with their defaults
    # (These would also be documented in your markdown)
    LAYOUT_CHOICES = [
        "text_left_image_right",
        "text_center_image_background",
        "text_only_centered",
        "text_right_image_left",
        "image_top_text_bottom",
        "image_only_full",
    ]
    DEFAULT_LAYOUT = "text_left_image_right"
    DEFAULT_IMAGE_ALT = "" # Should ideally be required if image_src is present
    DEFAULT_BG_COLOR = None # Or a specific default like "transparent" or "white"
    DEFAULT_TEXT_COLOR = "white" # Or a specific default
    DEFAULT_TEXT_BG_COLOR = "black-25"
    DEFAULT_MIN_HEIGHT = "auto"
    DEFAULT_CONTENT_ALIGN_VERTICAL = "center"

    # Video defaults (even if deferred for MVP, good to have placeholders)
    # TODO: Add video support
    DEFAULT_VIDEO_AUTOPLAY = False # Changed from true as per our discussion
    DEFAULT_VIDEO_LOOP = True
    DEFAULT_VIDEO_MUTED = True # Essential if autoplay is true
    DEFAULT_VIDEO_CONTROLS = False


    def get_context(self):
        context = super().get_context() # Gets basic context like 'content', 'kwargs'

        # --- Layout ---
        layout = self.kwargs.get("layout", self.DEFAULT_LAYOUT).lower()
        if layout not in self.LAYOUT_CHOICES:
            logger.error(
                f"HeroBlock: Invalid 'layout' parameter: '{layout}'. "
                f"Defaulting to '{self.DEFAULT_LAYOUT}'."
            )
            layout = self.DEFAULT_LAYOUT
        context["layout"] = layout

        # --- Image ---
        context["image_src"] = self.kwargs.get("image_src")
        image_alt = self.kwargs.get("image_alt", self.DEFAULT_IMAGE_ALT)
        if context["image_src"] and not image_alt:
            logger.warning(
                "HeroBlock: 'image_src' is present but 'image_alt' is missing or empty. "
                "Alt text is important for accessibility."
            )
            # You might choose to provide a generic alt or leave it as is, but log it.
        context["image_alt"] = image_alt

        # --- Styling & Dimensions (MVP) ---
        context["bg_color"] = self.kwargs.get("bg_color", self.DEFAULT_BG_COLOR)
        context["text_color"] = self.kwargs.get("text_color", self.DEFAULT_TEXT_COLOR)
        context["text_bg_color"] = self.kwargs.get("text_bg_color", self.DEFAULT_TEXT_BG_COLOR)
        context["min_height"] = self.kwargs.get("min_height", self.DEFAULT_MIN_HEIGHT)
        context["content_align_vertical"] = self.kwargs.get(
            "content_align_vertical", self.DEFAULT_CONTENT_ALIGN_VERTICAL
        ).lower()
        context["custom_class"] = self.kwargs.get("class", "") # User-provided custom classes

        # The 'content' variable (inner markdown processed to HTML) is already in context
        # from BasicSpellBlock's get_context.

        # Determine a CSS class for the layout for easier styling
        context["layout_class"] = f"sb-hero-layout--{layout.replace('_', '-')}"

        # Determine CSS class for vertical alignment
        align_map = {
            "top": "sb-items-start", # Assuming Flexbox/Grid alignment utilities
            "center": "sb-items-center",
            "bottom": "sb-items-end",
        }
        context["vertical_align_class"] = align_map.get(context["content_align_vertical"], "sb-items-center")

        return context
    
@SpellBlockRegistry.register()
class AlignBlock(BasicSpellBlock):
    name = "align"
    template = "django_spellbook/blocks/align.html" # Make sure this template is updated

    DEFAULT_POS = "center"
    DEFAULT_WIDTH = "100%" # Default is fully qualified
    DEFAULT_HEIGHT = "auto"   # Default is 'auto'
    DEFAULT_CONTENT_ALIGN = "center"

    def _process_dimension_value(self, value_str, default_value_with_unit):
        """
        Processes a dimension string (for width or height) to apply units.
        - "auto" remains "auto".
        - Explicit units like "50%", "120px" are validated and returned.
        - Unitless numbers <= 100 become "NN%".
        - Unitless numbers > 100 become "NNpx".
        - Invalid values fall back to default_value_with_unit.
        """
        # 1. Handle "auto" case-insensitively
        if str(value_str).lower() == "auto":
            return "auto"

        # 2. Check for explicit units (e.g., "50%", "120px")
        # Regex to match a number (int or float) followed by "px" or "%"
        # Allows for optional space before unit, case-insensitive units
        match = re.fullmatch(r"(-?\d*\.?\d+)\s*(px|%)", str(value_str), re.IGNORECASE)
        if match:
            number_part, unit = match.groups()
            # Validate that the number part is indeed a number
            float(number_part)
            return f"{number_part}{unit.lower()}" # Return as is, but with unit lowercased

        # 3. Handle numeric input (no unit provided by user)
        try:
            num = float(value_str)
            # Handle negative numbers - typically dimensions shouldn't be negative.
            # You might choose to treat them as 0 or use the default.
            if num < 0:
                logger.warning(f"Negative dimension value '{value_str}' received. Using '0%' or default. Forcing 0 for now.")
                # Or return default_value_with_unit
                return "0%" # Or "0px" depending on context, but % is safer for 0

            if num <= 100:
                # Format to avoid ".0%" for whole numbers
                return f"{int(num) if num.is_integer() else num}%"
            else: # num > 100
                return f"{int(num) if num.is_integer() else num}px"
        except ValueError:
            # Not "auto", not a recognized number+unit, not a simple number.
            logger.error(f"Unrecognized dimension value: '{value_str}'. Using default: '{default_value_with_unit}'.")
            return default_value_with_unit
        except TypeError: # Handles if value_str is None or other non-string/non-numeric type
            logger.error(f"Invalid type for dimension value: '{value_str}'. Using default: '{default_value_with_unit}'.")
            return default_value_with_unit


    def get_context(self):
        context = super().get_context()

        # Position
        pos = self.kwargs.get("pos", self.DEFAULT_POS).lower()
        if pos not in ["start", "center", "end"]: # These correspond to flex justify-content values
            logger.error(f"AlignBlock: Invalid 'pos' parameter: '{pos}'. Defaulting to '{self.DEFAULT_POS}'.")
            pos = self.DEFAULT_POS
        # Map to CSS flexbox justify-content values if needed, or use directly if your CSS handles start/end
        # Assuming 'start' -> 'flex-start', 'end' -> 'flex-end', 'center' -> 'center'
        # For simplicity, if your CSS uses "start", "center", "end" directly for justify-content, no change here.
        # If CSS expects flex-start/flex-end:
        if pos == "start":
            context["pos_css"] = "flex-start"
        elif pos == "end":
            context["pos_css"] = "flex-end"
        else: # center
            context["pos_css"] = "center"

        context["pos"] = context["pos_css"] # Overwriting pos with the CSS value


        # Width and Height using the new processing method
        raw_width = self.kwargs.get("width", self.DEFAULT_WIDTH)
        context["width"] = self._process_dimension_value(raw_width, self.DEFAULT_WIDTH)

        raw_height = self.kwargs.get("height", self.DEFAULT_HEIGHT)
        context["height"] = self._process_dimension_value(raw_height, self.DEFAULT_HEIGHT)

        # Content Alignment
        content_align = self.kwargs.get("content_align", self.DEFAULT_CONTENT_ALIGN).lower()
        if content_align not in ["start", "center", "end"]:
            logger.error(f"AlignBlock: Invalid 'content_align' parameter: '{content_align}'. Defaulting to '{self.DEFAULT_CONTENT_ALIGN}'.")
            content_align = self.DEFAULT_CONTENT_ALIGN
        # Map to CSS text-align values
        if content_align == "start":
            context["content_align_css"] = "left"
        elif content_align == "end":
            context["content_align_css"] = "right"
        else: # center
            context["content_align_css"] = "center"
        # The template you provided uses `{% if content_align == 'start' %}left{% ... %}`
        # So it's better to pass the original 'start', 'center', 'end' for content_align
        context["content_align"] = content_align


        # Standard string/optional parameters
        context["class"] = self.kwargs.get("class", None)
        context["id"] = self.kwargs.get("id", None)
        context["content_class"] = self.kwargs.get("content_class", None)

        return context
    
@SpellBlockRegistry.register()
class ButtonBlock(BasicSpellBlock):
    name = "button"
    template = "django_spellbook/blocks/button.html"  # You'll create this template next

    # Define default values for parameters
    DEFAULT_TYPE = "default"
    DEFAULT_SIZE = "md"

    def get_context(self):
        context = super().get_context()

        # --- Core Parameters ---
        href = self.kwargs.get("href")
        context["href"] = href

        # --- Styling and Behavior Parameters ---
        button_type = self.kwargs.get("type", self.DEFAULT_TYPE).lower()
        # Basic validation for common types, can be expanded with your CSS.
        # These will map to CSS classes like sb-button-primary, sb-button-default.
        # You might want a predefined list of valid types if your CSS is strict.
        context["button_type"] = button_type

        button_size = self.kwargs.get("size", self.DEFAULT_SIZE).lower()
        # These will map to CSS classes like sb-button-sm, sb-button-lg.
        context["button_size"] = button_size

        context["target"] = self.kwargs.get("target", None) # e.g., "_blank"

        disabled_str = self.kwargs.get("disabled", "false").lower()
        context["disabled"] = disabled_str == "true"
        # If disabled, the template might omit href or add specific ARIA attributes.

        # --- Icon Parameters ---
        context["icon_left"] = self.kwargs.get("icon_left", None)
        context["icon_right"] = self.kwargs.get("icon_right", None)

        # --- Customization ---
        context["custom_class"] = self.kwargs.get("class", None) # Renamed to avoid conflict with Python 'class'
        context["id"] = self.kwargs.get("id", None)
        
        # --- Tag Type ---
        # For this simplified version, it's always an 'a' tag.
        # If you later expand to support <button>, this could be dynamic.
        context["is_anchor"] = True 

        return context