from django.urls import path
from . import views

urlpatterns = [
    path('test', views.view_test, name='view_test')
]