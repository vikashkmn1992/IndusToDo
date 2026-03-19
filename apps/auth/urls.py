"""
Auth URLs.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, signup_view

app_name = 'auth'

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', signup_view, name='signup'),
]
