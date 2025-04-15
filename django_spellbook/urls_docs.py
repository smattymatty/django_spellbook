from django.urls import path
        
app_name = 'docs'
from django_spellbook.views_docs import *

urlpatterns = [
    path('intro/', intro, name='intro')
]