from django.urls import path
from . import views

urlpatterns = [
    path('introduction', views.view_introduction, name='view_introduction'),
    path('djangolike', views.view_djangolike, name='view_djangolike'),
    path('blocks', views.view_blocks, name='view_blocks'),
    path('sb/meta_toc', views.view_sb_meta_toc, name='view_sb_meta_toc'),
    path('sb/sb_intro', views.view_sb_sb_intro, name='view_sb_sb_intro'),
    path('sb/spellblocks', views.view_sb_spellblocks, name='view_sb_spellblocks')
]