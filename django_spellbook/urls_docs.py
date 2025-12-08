from django.urls import path

app_name = 'docs'
from django_spellbook.views_docs import *

urlpatterns = [
    path('intro/', view_intro, name='intro')
]