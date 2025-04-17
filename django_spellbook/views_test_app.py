import datetime
from django.shortcuts import render

# Table of Contents for test_app
TOC = {'title': 'root', 'url': '', 'children': {'test': {'title': 'Test Page', 'url': 'test_app:test'}}}


def test(request):
    context = {'title': 'Test Page', 'created_at': 'datetime.datetime(2025, 4, 17, 12, 24, 54, 527022)', 'updated_at': 'datetime.datetime(2025, 4, 17, 12, 24, 54, 527022)', 'url_path': 'test', 'raw_content': '# Test Heading\n\nThis is a test markdown file with some content.', 'is_public': True, 'tags': [], 'custom_meta': {'description': 'A test markdown page', 'created_at': datetime.date(2023, 1, 1)}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC 
    context['current_url'] = 'test'
    context['metadata'] = {
        'title': 'Test Page',
        'created_at': datetime.datetime(2025, 4, 17, 12, 24, 54, 527022),
        'updated_at': datetime.datetime(2025, 4, 17, 12, 24, 54, 527022),
        'url_path': 'test',
        'raw_content': '# Test Heading\n\nThis is a test markdown file with some content.',
        'is_public': True,
        'tags': [],
        'custom_meta': {'description': 'A test markdown page', 'created_at': datetime.date(2023, 1, 1)},
        'namespace': 'test_app',
        'url_name': 'test',
        'namespaced_url': 'test_app:test',
    }
    return render(request, 'test_app/spellbook_md/test.html', context)
