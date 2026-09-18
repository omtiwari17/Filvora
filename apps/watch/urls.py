from django.urls import path
from . import views

app_name = 'watch'

urlpatterns = [
    path('save/', views.save_progress, name='save_progress'),
    path('remove/', views.remove_progress, name='remove_progress'),
    path('history/', views.history_view, name='history'),
    path('history/clear/', views.clear_history, name='clear_history'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('mark-watched/', views.toggle_watched, name='toggle_watched'),
    path('collection/mark-watched/', views.toggle_collection_watched, name='toggle_collection_watched'),
    path('rate/', views.rate_content, name='rate_content'),
    path('rate/remove/', views.remove_rating, name='remove_rating'),
    path('collection/rate/', views.rate_collection, name='rate_collection'),
    path('collection/rate/remove/', views.remove_collection_rating, name='remove_collection_rating'),
]

