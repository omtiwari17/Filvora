from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.my_list, name='list'),
    path('toggle/', views.toggle_item, name='toggle'),
    path('collection/toggle-all/', views.toggle_collection_library, name='toggle_collection_library'),
    path('collection/create/', views.create_collection, name='create_collection'),
    path('collection/<int:collection_id>/delete/', views.delete_collection, name='delete_collection'),
    path('bookmark/add/', views.add_bookmark, name='add_bookmark'),
    path('bookmark/<int:bookmark_id>/delete/', views.delete_bookmark, name='delete_bookmark'),
    path('person/toggle/', views.toggle_favorite_person, name='toggle_favorite_person'),
    path('person/<int:person_id>/delete/', views.delete_favorite_person, name='delete_favorite_person'),
]
