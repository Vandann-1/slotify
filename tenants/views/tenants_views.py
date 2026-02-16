from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tenants.models import Tenant
from rest_framework.permissions import IsAuthenticated




class CreateWorkspaceView(APIView):
    """
    POST /api/workspaces/create/
    Create a new workspace
    
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):

        name = request.data.get("name")
        tenant_type = request.data.get("tenant_type")

        workspace = Tenant.objects.create(
            name=name,
            tenant_type=tenant_type,
            owner=request.user   # critical
        )
        team_size = request.data.get("team_size", "just_me")
        workspace.team_size = team_size
        workspace.save()
        

        # link user to workspace
        request.user.workspace = workspace
        request.user.save()

        return Response({
            "workspace_id": str(workspace.id),
            "slug": workspace.slug
        })




# ============================================================================================
# LIST WORKSPACES - this will be used in workspace list page to show all workspaces of the user
# ============================================================================================
from rest_framework.permissions import IsAuthenticated


class ListWorkspaceView(APIView):

    permission_classes = [IsAuthenticated]

    """
    GET /api/workspaces/

    List workspaces belonging to logged-in user
    """

    def get(self, request):
        user = request.user
        # if user has single workspace
        workspace = user.workspace

        data = [{
            "id": str(workspace.id),
            "name": workspace.name,
            "team_size": workspace.team_size,
            "slug": workspace.slug,
            "tenant_type": workspace.tenant_type,
            "email": workspace.email,
            "phone": workspace.phone,
            
        }]

        return Response(data)


class WorkspaceDetailView(APIView):
    """
    GET /api/workspaces/<slug>/
    
    Get single workspace
    from react side we will call this api 
    when user click on workspace from workspace list
    page to get workspace details
    """

    def get(self, request, slug):

        try:
            workspace = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": str(workspace.id),
            "name": workspace.name,
            "slug": workspace.slug,
            "tenant_type": workspace.tenant_type,
            "email": workspace.email,
            "phone": workspace.phone,
        })

class UpdateWorkspaceView(APIView):
    """
    PUT /api/workspaces/<slug>/update/
    
    Update workspace details like name, tenant_type, email, phone etc.
    We will not allow to update slug because it is used as 
    unique identifier for workspace and also
    used in url to access workspace details.
    If we allow to update slug then it will 
    create confusion for react side to access workspace details 
    because react side will be using old slug to access workspace details 
    which will not work after slug is updated.
    """

    def put(self, request, slug):

        try:
            workspace = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        name = request.data.get("name")
        tenant_type = request.data.get("tenant_type")
        email = request.data.get("email")
        phone = request.data.get("phone")

        if name:
            workspace.name = name
        if tenant_type:
            workspace.tenant_type = tenant_type
        if email:
            workspace.email = email
        if phone:
            workspace.phone = phone

        workspace.save()

        return Response({
            "id": str(workspace.id),
            "name": workspace.name,
            "slug": workspace.slug,
            "tenant_type": workspace.tenant_type,
            "email": workspace.email,
            "phone": workspace.phone,
        })