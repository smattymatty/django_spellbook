# django_spellbook/markdown/content_metrics.py

def get_word_count(content: str) -> int:
    """Get word count of content"""
    return len(content.split())


def get_reading_time_minutes(content: str) -> int:
    """Get reading time in minutes of content"""
    result: int = len(content.split()) / 215
    if result < 1:
        return 1
    return round(result)

