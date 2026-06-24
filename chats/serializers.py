from rest_framework import serializers
from django.contrib.auth import get_user_model
from tenants.context import get_current_tenant
from tenants.models import TenantMember
from .models import ChatRoom, Message

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]

class ChatRoomSerializer(serializers.ModelSerializer):
    members = UserMiniSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        many=True,
        source="members"
    )

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "is_group", "members", "member_ids", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No active tenant context.")
            
        members = attrs.get("members", [])
        if members:
            member_ids = [u.id for u in members]
            active_members_count = TenantMember.objects.filter(
                tenant=tenant,
                user_id__in=member_ids,
                is_active=True
            ).count()
            
            if active_members_count != len(member_ids):
                raise serializers.ValidationError("Some members do not belong to this workspace/tenant.")
            
        return attrs

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "room", "sender", "content", "is_read", "created_at"]
        read_only_fields = ["id", "room", "sender", "is_read", "created_at"]
