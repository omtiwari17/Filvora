from django.urls import path
from . import views

app_name = 'playback'

urlpatterns = [
    path('<str:media_type>/<int:tmdb_id>/', views.watch, name='watch'),
]
