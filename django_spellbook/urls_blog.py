from django.urls import path
from django_spellbook import views_blog as views

app_name = 'blog'

urlpatterns = [
    path('first-post/', views.view_first_post, name='first-post'),
    path('', views.directory_index_root_blog, name='blog_directory_index_directory_index_root_blog'),
]