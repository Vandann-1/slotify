from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def home(request):
    return HttpResponse("Slotify backend is running")

urlpatterns = [

    path("", home),  # <-- THIS FIXES YOUR PROBLEM

    path("admin/", admin.site.urls),
    path("api/", include("tenants.urls.tenants_urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/invitations/", include("invitations.urls")),

    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
]