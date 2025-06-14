import datetime
from django.shortcuts import render

# Table of Contents for docs
TOC = {'title': 'root', 'url': '', 'children': {'intro': {'title': 'Documentation Intro', 'url': 'docs:intro'}}}


def view_intro(request):
    context = {'title': 'Documentation Intro', 'url_path': 'intro', 'raw_content': '# Welcome to Docs\nThis is documentation.', 'published': None, 'modified': None, 'is_public': True, 'tags': [], 'author': None, 'custom_meta': {}, 'next_page': None, 'prev_page': None, 'word_count': 6, 'reading_time_minutes': 1}
    context['toc'] = TOC 
    context['current_url'] = 'intro'
    context['metadata'] = {
        'title': 'Documentation Intro',
        'published': None,
        'modified': None,
        'url_path': 'intro',
        'raw_content': '# Welcome to Docs\nThis is documentation.',
        'is_public': True,
        'tags': [],
        'author': None,
        'custom_meta': {},
        'namespace': 'docs',
        'url_name': 'intro',
        'namespaced_url': 'docs:intro',
        'word_count': 6,
        'reading_time_minutes': 1,
    }
    return render(request, 'docs/spellbook_md/intro.html', context)
