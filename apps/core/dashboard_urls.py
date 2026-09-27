from django.urls import path
from .admin_dashboard import (
    admin_dashboard_view,
    admin_purge_cache,
    admin_ping_tmdb,
    admin_check_db,
    admin_reset_circuit_breaker,
    admin_logs_stream,
    admin_quick_inspect,
)

urlpatterns = [
    path('', admin_dashboard_view, name='admin_dashboard'),
    path('purge-cache/', admin_purge_cache, name='admin_purge_cache'),
    path('ping-tmdb/', admin_ping_tmdb, name='admin_ping_tmdb'),
    path('check-db/', admin_check_db, name='admin_check_db'),
    path('reset-breaker/', admin_reset_circuit_breaker, name='admin_reset_circuit_breaker'),
    path('logs/', admin_logs_stream, name='admin_logs_stream'),
    path('inspect/', admin_quick_inspect, name='admin_quick_inspect'),
]
