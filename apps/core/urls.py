from django.urls import path
from .views import HomeView, RecommendationsView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('recommendations/', RecommendationsView.as_view(), name='recommendations'),
]

