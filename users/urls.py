from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from users.views import UserRegistration


urlpatterns = [
    path('register/', UserRegistration.as_view(), name="user-registration")
]