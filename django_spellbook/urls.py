from django.urls import path, include

urlpatterns = [
    path('docs/', include('django_spellbook.urls_docs')),
    path('blog/', include('django_spellbook.urls_blog'))
]
