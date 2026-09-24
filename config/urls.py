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
    path('watch/remove/', watch_views.remove_progress, name='watch_remove_progress'),
    path('watch/history/', watch_views.history_view, name='watch_history'),
    path('watch/history/clear/', watch_views.clear_history, name='watch_clear_history'),
    path('watch/', include('apps.playback.urls')),
    path('progress/', include('apps.watch.urls')),
    path('history/', watch_views.history_view, name='history'),
    path('history/clear/', watch_views.clear_history, name='clear_history'),
    path('history/remove/', watch_views.remove_progress, name='history_remove_progress'),
    path('analytics/', watch_views.analytics_view, name='analytics'),
    # path('downloads/', include('apps.downloads.urls')),  # [ON HOLD / DROPPED]
    path('', include('apps.catalog.urls')),
    path('', include('apps.core.urls')),
]
