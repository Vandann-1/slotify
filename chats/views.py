from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from tenants.permissions import IsTenantMember
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        # Automatically filtered by current tenant via TenantAwareModel & TenantManager!
        return ChatRoom.objects.all().order_by("-updated_at")

    def perform_create(self, serializer):
        # Tenant is automatically injected during save() by TenantAwareModel!
        room = serializer.save()
        # Ensure creator is added to members
        room.members.add(self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        room = self.get_object()
        # Message is also a TenantAwareModel, so queries on it are tenant-isolated automatically
        messages = room.messages.all().order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
