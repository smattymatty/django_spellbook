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
