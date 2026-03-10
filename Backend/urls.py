from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def home(request):
    return JsonResponse({"status": "Slotify backend running"})


urlpatterns = [

    path("", home),

    path("admin/", admin.site.urls),

    path("api/", include("tenants.urls.tenants_urls")),
    path("api/", include("plans_subsci.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/invitations/", include("invitations.urls")),

    path("api-auth/", include("rest_framework.urls")),

    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain"
    ),

    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
]