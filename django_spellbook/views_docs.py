import datetime
from django.shortcuts import render

# Table of Contents for docs
TOC = {'title': 'root', 'url': '', 'children': {'intro': {'title': 'Documentation Intro', 'url': 'docs:intro'}}}


def view_intro(request):
    context = {'title': 'Documentation Intro', 'url_path': 'intro', 'raw_content': '# Welcome to Docs\nThis is documentation.', 'published': None, 'modified': None, 'is_public': True, 'tags': [], 'author': None, 'custom_meta': {}, 'next_page': None, 'prev_page': None, 'word_count': 6, 'reading_time_minutes': 1}
    context['toc'] = TOC
    context['current_url'] = 'docs:intro'
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
        'prev_page': None,
        'next_page': None,
    }
    context['parent_directory_url'] = 'docs:docs_directory_index_directory_index_root_docs'
    context['parent_directory_name'] = 'Docs'
    return render(request, 'docs/spellbook_md/intro.html', context)


def directory_index_root_docs(request):
    """Auto-generated directory index view for """
    context = {
    'directory_name': 'Docs',
    'directory_path': '',
    'parent_dir_url': None,
    'parent_dir_name': None,
    'subdirectories': [],
    'pages': [
        {
            'title': 'Documentation Intro',
            'url': 'intro/',
            'published': None,
            'modified': None,
            'tags': [],
            'description': None,
        },
    ],
}
    return render(request, 'django_spellbook/directory_index/default.html', context)
