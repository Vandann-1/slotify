from rest_framework import viewsets, permissions, status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from Backend.permissions import IsTenantMember
from .models import Conversation, Message
from .serializers import ConversationListSerializer, MessageSerializer



class ConversationViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows conversations to be viewed.
    """
    permission_classes = [permissions.IsAuthenticated,] 
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(member=user).order_by('-last_message_at')

    

class MessageListAPIView(ListAPIView):
    """
    API endpoint that allows messages to be viewed.

    """
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    serializer_class = MessageSerializer


    def get_queryset(self):
        user = self.request.user
        conversation_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(conversation_id=conversation_id, conversation__member=user).order_by('created_at')

    
