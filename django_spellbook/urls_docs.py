from django.urls import path
from django_spellbook import views_docs as views

app_name = 'docs'

urlpatterns = [
    path('intro/', views.view_intro, name='intro'),
    path('', views.directory_index_root_docs, name='docs_directory_index_root_docs'),
]