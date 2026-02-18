from django.urls import path, include
from rest_framework.routers import DefaultRouter

from tenants.views.tenants_views import TenantViewSet
# this file is for tenants app urls, it will be included in the main urls.py file of the project

'''this router is used to register
the tenant viewset, it will automatically
generate the urls for the tenant viewset.'''

router = DefaultRouter()


router.register("workspaces", TenantViewSet, basename="workspaces")

urlpatterns = [
    path("", include(router.urls)),
]
