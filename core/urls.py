from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("residence_connectee.urls")),
    # # Validate user credentials and obtain Access and Refresh tokens
    path("api/token/", TokenObtainPairView.as_view()),
    # Get a new Access token using the Refresh token
    path("api/token/refresh/", TokenRefreshView.as_view())
]