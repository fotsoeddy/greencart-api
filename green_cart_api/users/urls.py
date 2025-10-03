from django.urls import path
from .api.views.user_view import (
    RegisterView, LoginView, RefreshTokenView, VerifyEmailView,
    ProfileRetrieveView, ProfileUpdateView, UserListView
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh-token/', RefreshTokenView.as_view(), name='token_refresh'),
    path('verify_email/', VerifyEmailView.as_view(), name='verify_email'),
    path('profile/', ProfileRetrieveView.as_view(), name='profile_retrieve'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('users/', UserListView.as_view(), name='user_list'),
]