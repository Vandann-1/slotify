from django.urls import path, include
from rest_framework.routers import DefaultRouter

from tenants.views.tenants_views import TenantViewSet
# this file is for tenants app urls, it will be included in the main urls.py file of the project
router = DefaultRouter()

router.register("", TenantViewSet, basename="workspaces")

urlpatterns = [
    path("", include(router.urls)),
]
