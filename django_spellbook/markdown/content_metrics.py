# django_spellbook/markdown/content_metrics.py

import re

def get_word_count(content: str) -> int:
    """
    Calculate the word count of the content, excluding the markup
    definitions of Spellbook blocks, but including the content
    *within* those blocks.

    Note: Django-like syntax ({% div %}) was removed in 0.2.0.
    This function maintains backward compatibility for legacy content.
    """
    if not content:
        return 0

    # 1. Replace Spellbook opening tags ({% raw %}{~ name attributes ~}{% endraw %}) with a space
    #    This removes the definition but leaves the content that follows.
    text_cleaned = re.sub(r'{\~.*?~}', ' ', content, flags=re.DOTALL)

    # 2. Replace Spellbook closing tags ({% raw %}{~~}{% endraw %}) with a space
    text_cleaned = re.sub(r'{\~~}', ' ', text_cleaned, flags=re.DOTALL)
    
    # 3. Replace Django-like tags ({% raw %}{% ... %}{% endraw %}) with a space
    #    This handles both opening tags like {% raw %}{% div %}{% endraw %} and closing tags like {% raw %}{% enddiv %}{% endraw %}.
    text_cleaned = re.sub(r'{%.*?%}', ' ', text_cleaned, flags=re.DOTALL)

    # 4. Count words in the remaining text
    words = re.findall(r'\w+', text_cleaned)

    return len(words)



def get_reading_time_minutes(content: str) -> int:
    """Get reading time in minutes of content"""
    result: int = len(content.split()) / 215
    if result < 1:
        return 1
    return round(result)

