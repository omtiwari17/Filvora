"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from apps.watch import views as watch_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('library/', include('apps.library.urls')),
    path('watch/', include('apps.playback.urls')),
    path('progress/', include('apps.watch.urls')),
    path('history/', watch_views.history_view, name='history'),
    path('history/clear/', watch_views.clear_history, name='clear_history'),
    path('analytics/', watch_views.analytics_view, name='analytics'),
    path('', include('apps.catalog.urls')),
    path('', include('apps.core.urls')),
]
