from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.my_list, name='list'),
    path('toggle/', views.toggle_item, name='toggle'),
    path('collection/create/', views.create_collection, name='create_collection'),
    path('collection/<int:collection_id>/delete/', views.delete_collection, name='delete_collection'),
    path('bookmark/add/', views.add_bookmark, name='add_bookmark'),
    path('bookmark/<int:bookmark_id>/delete/', views.delete_bookmark, name='delete_bookmark'),
]
