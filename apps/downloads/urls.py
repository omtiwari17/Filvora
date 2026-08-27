from django.urls import path
from . import views

app_name = 'downloads'

urlpatterns = [
    path('', views.downloads_dashboard, name='dashboard'),
    path('start/', views.start_download, name='start'),
    path('status/', views.download_status_partial, name='status'),
    path('file/<uuid:job_id>/', views.download_file, name='file'),
    path('cancel/<uuid:job_id>/', views.cancel_download, name='cancel'),
]
