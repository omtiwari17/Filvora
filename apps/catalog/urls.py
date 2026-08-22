from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('movies/', views.movie_browse, name='movie_browse'),
    path('movies/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
    path('series/', views.series_browse, name='series_browse'),
    path('series/<int:tmdb_id>/', views.series_detail, name='series_detail'),
    path('series/<int:tmdb_id>/season/<int:season_number>/', views.season_episodes, name='season_episodes'),
]
