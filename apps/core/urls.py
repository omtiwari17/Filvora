from django.urls import path
from .views import HomeView, RecommendationsView, ServerHubView, server_hub_log, phone_server_access_view

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('recommendations/', RecommendationsView.as_view(), name='recommendations'),
    path('server-access/', phone_server_access_view, name='phone_server_access'),
    path('phone-server/', phone_server_access_view, name='phone_server_alias'),
    path('server-hub/', ServerHubView.as_view(), name='server_hub'),
    path('server-hub/log/', server_hub_log, name='server_hub_log'),
]

