from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel

User = settings.AUTH_USER_MODEL


class Conversation(TenantAwareModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    booking = models.ForeignKey('booking.Booking', on_delete=models.CASCADE, related_name='conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_conversations')

    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('archived', 'Archived'), ('closed', 'Closed')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    last_message_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation: {self.name or str(self.id)} (Tenant: {self.tenant})"


class Message(TenantAwareModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=50, default='text')  # e.g., text, image, file
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} in conversation {self.conversation_id}"
