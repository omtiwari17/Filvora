from django.urls import path
from . import views

app_name = 'playback'

urlpatterns = [
    path('<str:media_type>/<int:tmdb_id>/', views.watch, name='watch'),
    path('tv/<int:tmdb_id>/<int:season>/<int:episode>/', views.watch, {'media_type': 'tv'}, name='watch_episode'),
]
