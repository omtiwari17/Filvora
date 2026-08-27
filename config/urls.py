"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('library/', include('apps.library.urls')),
    path('watch/', include('apps.playback.urls')),
    path('progress/', include('apps.watch.urls')),
    path('', include('apps.catalog.urls')),
    path('', include('apps.core.urls')),
]
