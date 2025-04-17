import datetime
from django.shortcuts import render

# Table of Contents for docs
TOC = {'title': 'root', 'url': '', 'children': {'intro': {'title': 'Documentation Intro', 'url': 'docs:intro'}}}


def intro(request):
    context = {'title': 'Documentation Intro', 'created_at': 'datetime.datetime(2025, 4, 17, 12, 41, 54, 885747)', 'updated_at': 'datetime.datetime(2025, 4, 17, 12, 41, 54, 885747)', 'url_path': 'intro', 'raw_content': '# Welcome to Docs\nThis is documentation.', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC 
    context['current_url'] = 'intro'
    context['metadata'] = {
        'title': 'Documentation Intro',
        'created_at': datetime.datetime(2025, 4, 17, 12, 41, 54, 885747),
        'updated_at': datetime.datetime(2025, 4, 17, 12, 41, 54, 885747),
        'url_path': 'intro',
        'raw_content': '# Welcome to Docs\nThis is documentation.',
        'is_public': True,
        'tags': [],
        'custom_meta': {},
        'namespace': 'docs',
        'url_name': 'intro',
        'namespaced_url': 'docs:intro',
    }
    return render(request, 'docs/spellbook_md/intro.html', context)
