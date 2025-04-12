from django.urls import path, include

urlpatterns = [
    path('test_app/', include('django_spellbook.urls_test_app')),
    path('docs_app/', include('django_spellbook.urls_docs_app')),
    path('blog_app/', include('django_spellbook.urls_blog_app')),
    path('docs/', include('django_spellbook.urls_docs')),
    path('blog/', include('django_spellbook.urls_blog'))
]
