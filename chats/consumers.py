from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from tenants.context import set_current_tenant, clear_current_tenant

from .models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Logged-in user
        self.user = self.scope["user"]

        # URL: ws/chat/<conversation_id>/
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        # Group name
        self.conversation_group_name = f"chat_{self.conversation_id}"

        # --------------------------------------------------
        # 1. Authentication
        # --------------------------------------------------
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        # --------------------------------------------------
        # 2. Load Conversation
        # --------------------------------------------------
        self.conversation = await self.get_conversation(
            self.conversation_id
        )

        if not self.conversation:
            await self.close(code=4004)
            return

        # --------------------------------------------------
        # 3. Verify user belongs to conversation
        # --------------------------------------------------
        allowed = await self.verify_conversation_participant(
            self.conversation,
            self.user,
        )

        if not allowed:
            await self.close(code=4003)
            return

        # --------------------------------------------------
        # 4. Join Channel Group
        # --------------------------------------------------
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "conversation_group_name"):
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name,
            )

    async def receive_json(self, content):
        message = content.get("message", "").strip()

        if not message:
            return

        # Optional length validation
        if len(message) > 5000:
            return

        saved_message = await self.save_message(
            conversation=self.conversation,
            sender=self.user,
            content=message,
        )

        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                "type": "chat_message",
                **saved_message,
            },
        )

    async def chat_message(self, event):
        await self.send_json(
            {
                "id": event["id"],
                "message": event["message"],
                "sender_id": event["sender_id"],
                "sender_username": event["sender_username"],
                "created_at": event["created_at"],
            }
        )

    # ======================================================
    # Database Helpers
    # ======================================================

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        try:
            return (
                Conversation.unfiltered_objects
                .select_related(
                    "tenant",
                    "user",
                    "member",
                    "last_message",
                )
                .get(id=conversation_id)
            )
        except (Conversation.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def verify_conversation_participant(self, conversation, user):
        return (
            conversation.user_id == user.id
            or conversation.member_id == user.id
        )

    @database_sync_to_async
    def save_message(self, conversation, sender, content):
        token = set_current_tenant(conversation.tenant)

        try:
            message = Message.objects.create(
                conversation=conversation,
                tenant=conversation.tenant,
                sender=sender,
                content=content,
            )

            # Update conversation metadata
            conversation.last_message = message
            conversation.last_message_at = message.created_at
            conversation.save(
                update_fields=[
                    "last_message",
                    "last_message_at",
                ]
            )

            return {
                "id": message.id,
                "message": message.content,
                "sender_id": sender.id,
                "sender_username": sender.username,
                "created_at": message.created_at.isoformat(),
            }

        finally:
            clear_current_tenant(token)