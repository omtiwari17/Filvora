from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.my_list, name='list'),
    path('toggle/', views.toggle_item, name='toggle'),
    path('collection/create/', views.create_collection, name='create_collection'),
    path('collection/<int:collection_id>/delete/', views.delete_collection, name='delete_collection'),
]
