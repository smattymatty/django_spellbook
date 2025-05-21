import datetime
from django.shortcuts import render

# Table of Contents for blog
TOC = {'title': 'root', 'url': '', 'children': {'first-post': {'title': 'First Post', 'url': 'blog:first-post'}}}


def view_first_post(request):
    context = {'title': 'First Post', 'url_path': 'first-post', 'raw_content': '# Blog Begins\nThis is our first blog post.', 'published': None, 'modified': None, 'is_public': True, 'tags': [], 'custom_meta': {}, 'next_page': None, 'prev_page': None, 'word_count': 8, 'reading_time_minutes': 1}
    context['toc'] = TOC 
    context['current_url'] = 'first-post'
    context['metadata'] = {
        'title': 'First Post',
        'published': None,
        'modified': None,
        'url_path': 'first-post',
        'raw_content': '# Blog Begins\nThis is our first blog post.',
        'is_public': True,
        'tags': [],
        'custom_meta': {},
        'namespace': 'blog',
        'url_name': 'first-post',
        'namespaced_url': 'blog:first-post',
        'word_count': 8,
        'reading_time_minutes': 1,
    }
    return render(request, 'blog/spellbook_md/first-post.html', context)
