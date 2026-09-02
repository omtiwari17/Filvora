from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profiles/', views.profiles_view, name='profiles'),
    path('profiles/create/', views.create_profile, name='create_profile'),
    path('profiles/<int:profile_id>/switch/', views.switch_profile, name='switch_profile'),
    path('profiles/<int:profile_id>/update/', views.update_profile, name='update_profile'),
    path('profiles/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
]
