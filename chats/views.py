from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from Backend.permissions import IsTenantMember
from .models import Conversation, Message
from .serializers import ConversationListSerializer, MessageSerializer



class ConversationListAPIView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows conversations to be viewed.
    """
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(members=user).order_by('-last_message_at')

    
class ConversationDetailAPIView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows a conversation to be viewed.
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        conversation_id = self.kwargs.get('pk')
        return Message.objects.filter(conversation_id=conversation_id, conversation__members=user).order_by('created_at')
    

class MessageListAPIView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows messages to be viewed.
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        conversation_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(conversation_id=conversation_id, conversation__members=user).order_by('created_at')

    
