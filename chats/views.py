from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from Backend.permissions import IsTenantMember
from .models import Conversation, Message
from .serializers import ConversationListSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationListSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        # Automatically filtered by current tenant via TenantAwareModel & TenantManager!
        return Conversation.objects.all().order_by("-updated_at")

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        # Message is also a TenantAwareModel, so queries on it are tenant-isolated automatically
        messages = conversation.messages.all().order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
