from rest_framework import permissions
from tenants.models.tenant import TenantMember
from tenants.choices import TenantMemberRole


class IsTenantMember(permissions.BasePermission):
    """
    Permission class that grants access only to active members of the active tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        # If the member was already resolved and attached to the request
        if getattr(request, "tenant_member", None):
            return True

        # Fallback query if simplejwt authentication ran after middleware
        try:
            member = TenantMember.objects.get(
                tenant=tenant,
                user=request.user,
                is_active=True
            )
            request.tenant_member = member
            return True
        except TenantMember.DoesNotExist:
            return False


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class that grants access only to Owners/Admins of the active tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        member = getattr(request, "tenant_member", None)
        if not member:
            try:
                member = TenantMember.objects.get(
                    tenant=tenant,
                    user=request.user,
                    is_active=True
                )
                request.tenant_member = member
            except TenantMember.DoesNotExist:
                return False

        return member.role in [TenantMemberRole.OWNER, TenantMemberRole.ADMIN]
