from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ConversationViewSet,
    MessageListAPIView,
)

router = DefaultRouter()
router.register(
    r"conversations",ConversationViewSet,basename="conversation",)

urlpatterns = [
    path("", include(router.urls)),

    path(
        "conversations/<int:conversation_pk>/messages/",
        MessageListAPIView.as_view(),
        name="conversation-messages",
    ),
]