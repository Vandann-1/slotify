from rest_framework import serializers
from django.contrib.auth import get_user_model
from tenants.context import get_current_tenant
from tenants.models import TenantMember
from .models import  Message , Conversation


User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]


class MessageSerializer(serializers.ModelSerializer):

    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "content", "is_read", "created_at"]
        read_only_fields = ["id", "sender", "is_read", "created_at"]


class ConversationListSerializer(serializers.ModelSerializer):
    last_message = MessageSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "name", "status", "last_message", "last_message_at"]
        read_only_fields = ["id", "name", "status", "last_message", "last_message_at"]

