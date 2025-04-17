from django.urls import path

app_name = 'test_app'
from django_spellbook.views_test_app import *

urlpatterns = [
    path('test/', test, name='test')
]