from django.shortcuts import render
from rest_framework import generics
from tenants.models import *
from tenants.serializers.tenant_serializer import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView



class CreateWorkspaceView(APIView):

    def post(self, request):

        name = request.data.get("name")
        tenant_type = request.data.get("tenant_type")
        email = request.data.get("email")
        phone = request.data.get("phone")

        # validation
        if not name:
            return Response(
                {"error": "Workspace name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not tenant_type:
            return Response(
                {"error": "Workspace type is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # create workspace (tenant)
        workspace = Tenant.objects.create(
            name=name,
            tenant_type=tenant_type,
            email=email,
            phone=phone
        )

        return Response(
            {
                "message": "Workspace created successfully",
                "workspace": {
                    "id": str(workspace.id),
                    "name": workspace.name,
                    "slug": workspace.slug,
                    "tenant_type": workspace.tenant_type,
                    "email": workspace.email,
                    "phone": workspace.phone,
                }
            },
            status=status.HTTP_201_CREATED
        )
        

class ListWorkspaceView(APIView):

    def get(self, request):

        workspaces = Tenant.objects.all()

        data = []

        for workspace in workspaces:
            data.append({
                "id": str(workspace.id),
                "name": workspace.name,
                "slug": workspace.slug,
                "tenant_type": workspace.tenant_type,
                "email": workspace.email,
                "phone": workspace.phone,
            })

        return Response(data)
        
        
        