from django.urls import path
from .api import AcceptInvitationAPIView, InviteProfessionalAPIView , ValidateInvitationAPIView

urlpatterns = [
    path("accept/", AcceptInvitationAPIView.as_view(), name="accept-invitation"),

    # ✅ NO api/ here
    path(
        "workspaces/<slug:slug>/invite/",
        InviteProfessionalAPIView.as_view(),
        name="invite-professional",
    ),
     path("validate/", ValidateInvitationAPIView.as_view(), name="validate-invitation"),
]