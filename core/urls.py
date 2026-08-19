from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",
         include("residence_connectee.urls")
    ),
    # # Validate user credentials and obtain Access and Refresh tokens
    path("api/token/",
         TokenObtainPairView.as_view(),
         name="token_obtain_pair"
    ),
    # Get a new Access token using the Refresh token
    path("api/token/refresh/",
         TokenRefreshView.as_view(),
         name="token_refresh"
    ),

    # Raw OpenAPI Scheme (YAML/JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI Interface
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Alternative ReDoc (static documentation-oriented view)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc')
]