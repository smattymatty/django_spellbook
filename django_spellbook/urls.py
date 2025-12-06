from django.urls import path, include

urlpatterns = [
    path('blog', include('django_spellbook.urls_blog')),
    path('', include('django_spellbook.urls_test_app'))
]
