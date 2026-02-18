from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class TenantViewSet(viewsets.ModelViewSet):
    '''this is a viewset for tenant model.
       it will be used to create and update tenants.
       it will also be used to list tenants.
       POST /api/workspaces/ - create a new tenant
       GET /api/workspaces/ - list all tenants of the user
       from react side we will use this viewset to create and list tenants.
       step 1: user will fill the form and submit it.
       step 2: we will send a POST request to /api/workspaces/ with the
               form data and the user token.
       step 3: if the request is successful we will get the tenant data in response.'''

    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"
    
    
    # THIS CONTROL WORKSPACE LIST
    # GET /api/workspaces/ - list workspaces of the user and also show the role of the user in the tenant.  
    # list workspaces of the user and also show the role of the user in the tenant.
    def get_queryset(self):

        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("Login to view your workspaces.")
            # return Tenant.objects.none()

        return Tenant.objects.filter(
            members__user=user,
            is_active=True
        ).distinct()

# CREATE WORKSPACE
# POST /api/workspaces/ - create a new tenant and also create a tenant member with the role of owner.
    def perform_create(self, serializer):

        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in.")

        serializer.save(owner=user)

    # GET SERIALIZED DATA WITH REQUEST CONTEXT
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    
    @action(detail=True, methods=["get"])    
    def dashboard(self, request, slug=None):
        tenant = self.get_object()
        
        # check if the user is a member of the tenant
        member = tenant.members.filter(user=request.user).first()
        return Response({"message": f"Welcome to the dashboard of {tenant.name}!"})    
