import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from tenants.context import set_current_tenant, clear_current_tenant
from tenants.models import TenantMember
from .models import ChatRoom, Message

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # 1. Reject if user is not authenticated
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4003)  # Forbidden
            return

        # 2. Get the room
        self.room = await self.get_room(self.room_id)
        if not self.room:
            await self.close(code=4004)  # Not Found
            return

        # 3. Verify member belongs to room's tenant/workspace
        is_member = await self.verify_tenant_membership(self.room.tenant, self.user)
        if not is_member:
            await self.close(code=4003)  # Forbidden
            return

        # 4. Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive_json(self, content):
        message_text = content.get("message", "").strip()
        if not message_text:
            return

        # Save message to database under the room's tenant context
        saved_msg = await self.save_message(self.room, self.user, message_text)

        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": saved_msg["content"],
                "sender_id": saved_msg["sender_id"],
                "sender_username": saved_msg["sender_username"],
                "created_at": saved_msg["created_at"],
                "id": saved_msg["id"]
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json({
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "created_at": event["created_at"],
            "id": event["id"]
        })

    @database_sync_to_async
    def get_room(self, room_id):
        try:
            return ChatRoom.unfiltered_objects.select_related("tenant").get(id=room_id)
        except (ChatRoom.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def verify_tenant_membership(self, tenant, user):
        return TenantMember.objects.filter(tenant=tenant, user=user, is_active=True).exists()

    @database_sync_to_async
    def save_message(self, room, sender, content):
        # Set tenant context explicitly for row-level isolation save
        token = set_current_tenant(room.tenant)
        try:
            msg = Message.objects.create(
                room=room,
                sender=sender,
                content=content
            )
            return {
                "id": msg.id,
                "content": msg.content,
                "sender_id": sender.id,
                "sender_username": sender.username,
                "created_at": msg.created_at.isoformat()
            }
        finally:
            clear_current_tenant(token)
