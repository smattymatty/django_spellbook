from django.urls import path
        
app_name = 'blog'
from django_spellbook.views_blog import *

urlpatterns = [
    path('first-post/', first_post, name='first-post')
]