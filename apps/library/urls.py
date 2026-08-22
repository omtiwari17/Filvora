from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.my_list, name='list'),
    path('toggle/', views.toggle_item, name='toggle'),
]
