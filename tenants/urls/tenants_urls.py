
from django.urls import path
from tenants.views.tenants_views import *


urlpatterns = [
   path("create/", CreateWorkspaceView.as_view()),
    path("list/", ListWorkspaceView.as_view()),
]