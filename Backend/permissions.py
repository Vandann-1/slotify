from rest_framework import permissions
from tenants.models.tenant import TenantMember
from tenants.choices import TenantMemberRole
from django.conf import settings

from django.contrib.auth.models import AnonymousUser


class IsTenantOwner(permissions.BasePermission):
    """
    Permission class that grants access only to the Owner of the active tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        return tenant.owner == request.user


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class that grants access to Owners/Admins of the active tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        if tenant.owner == request.user:
            return True

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


class IsTenantProfessional(permissions.BasePermission):
    """
    Permission class that grants access to Tenant Members with roles:
    Owner, Admin, or Professional.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        if tenant.owner == request.user:
            return True

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

        return member.role in [TenantMemberRole.OWNER, TenantMemberRole.ADMIN, TenantMemberRole.PROFESSIONAL]


class IsTenantMember(permissions.BasePermission):
    """
    Permission class that grants access to any active member of the active tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        if tenant.owner == request.user:
            return True

        if getattr(request, "tenant_member", None):
            return True

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