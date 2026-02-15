from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



urlpatterns = [
    path("admin/", admin.site.urls),

    # login/logout
    path("accounts/", include("django.contrib.auth.urls")),

     path("accounts/", include("accounts.urls")),

    # web app
    path("", include("Tracker.urls")),

    # API
    path("api/", include("Tracker.api_urls")),
    
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
]
