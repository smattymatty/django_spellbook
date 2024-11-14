import datetime
from django.shortcuts import render

# Table of Contents for all views
TOC = {'test': 'toc'}


def view_test(request):
    context = {'title': 'Test', 'created_at': 'datetime.datetime(2024, 11, 10, 3, 29, 58, 8432)', 'updated_at': 'datetime.datetime(2024, 11, 10, 3, 29, 58, 8432)', 'url_path': 'test', 'raw_content': '# Test\nThis is a test', 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None}
    context['toc'] = TOC  # Use the module-level TOC variable
    return render(request, 'test_app/spellbook_md/test.html', context)
