from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('discover/', views.discover, name='discover'),
    path('surprise-me/', views.surprise_me, name='surprise_me'),
    path('genres/', views.genres_view, name='genres'),
    path('movies/', views.movie_browse, name='movie_browse'),
    path('movies/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
    path('series/', views.series_browse, name='series_browse'),
    path('series/<int:tmdb_id>/', views.series_detail, name='series_detail'),
    path('series/<int:tmdb_id>/season/<int:season_number>/', views.season_episodes, name='season_episodes'),
    path('person/<int:person_id>/', views.person_detail, name='person_detail'),
    path('trailer/<str:media_type>/<int:tmdb_id>/', views.trailer_api, name='trailer_api'),
    path('search/', views.search_results, name='search_results'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
]
