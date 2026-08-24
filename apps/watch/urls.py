from django.urls import path
from . import views

app_name = 'watch'

urlpatterns = [
    path('save/', views.save_progress, name='save_progress'),
    path('remove/', views.remove_progress, name='remove_progress'),
]
