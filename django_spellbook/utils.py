from django.conf import settings


def remove_leading_dash(url: str) -> str:
    return url.lstrip('-') 


def titlefy(text: str) -> str:
    """Capitalize the first letter of each word in a string if it's longet than 2 chars.
    Also replace any dashes with spaces."""
    if not getattr(settings, 'SPELLBOOK_MD_TITLEFY', True):
        return text

    space_words = text.split(' ')
    dash_words = text.split('-')

    if len(dash_words) > 1:
        words = dash_words
    else:
        words = space_words

    capitalized_words = []
    for word in words:
        if len(word) > 2:
            capitalized_words.append(word.capitalize())
        else:
            capitalized_words.append(word)

    return ' '.join(capitalized_words)
