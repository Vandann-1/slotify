from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel

User = settings.AUTH_USER_MODEL

class ChatRoom(TenantAwareModel):
    name = models.CharField(max_length=255, blank=True)
    is_group = models.BooleanField(default=False)
    members = models.ManyToManyField(User, related_name="chat_rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.is_group:
            return f"Group Room: {self.name} (Tenant: {self.tenant})"
        return f"Direct Room: {self.name or str(self.id)} (Tenant: {self.tenant})"

class Message(TenantAwareModel):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} in room {self.room.id}"
