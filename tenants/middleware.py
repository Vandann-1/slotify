from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ObjectDoesNotExist
from tenants.models.tenant import Tenant, TenantMember
from tenants.context import set_current_tenant, clear_current_tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that identifies the active tenant from headers, query params, or subdomain,
    and sets the tenant context for thread-safe access.
    """

    def process_request(self, request):
        tenant = None

        # 1. Resolve from custom header (preferred for client apps)
        tenant_slug = request.headers.get("X-Tenant-Slug") or request.headers.get("X-Workspace-Slug")

        # 2. Fallback to query parameters
        if not tenant_slug:
            tenant_slug = request.GET.get("workspace_slug") or request.GET.get("tenant_slug")

        # 3. Fallback to subdomain (e.g. workspace.slotify.com)
        if not tenant_slug:
            host = request.get_host().split(":")[0]
            parts = host.split(".")
            # If subdomain exists (excluding common ones like www, api, mail, admin)
            if len(parts) > 2 and parts[0] not in ["www", "api", "admin", "mail"]:
                tenant_slug = parts[0]

        # 4. Resolve the tenant object from DB
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                pass

        # Attach to the request object
        request.tenant = tenant
        request.tenant_member = None

        # Bind to the thread-safe context
        if tenant:
            request._tenant_context_token = set_current_tenant(tenant)

            # Check if user is authenticated (for Session-based authentications)
            if hasattr(request, "user") and request.user.is_authenticated:
                try:
                    request.tenant_member = TenantMember.objects.get(
                        tenant=tenant,
                        user=request.user,
                        is_active=True
                    )
                except TenantMember.DoesNotExist:
                    pass
        else:
            # If no tenant header is provided, check if the user has a default/only workspace
            # (only possible if user is already authenticated by session middleware)
            if hasattr(request, "user") and request.user.is_authenticated:
                # Find the first active membership
                first_membership = TenantMember.objects.filter(
                    user=request.user,
                    is_active=True,
                    tenant__is_active=True
                ).select_related("tenant").first()
                if first_membership:
                    request.tenant = first_membership.tenant
                    request.tenant_member = first_membership
                    request._tenant_context_token = set_current_tenant(first_membership.tenant)

    def process_response(self, request, response):
        """
        Ensure the thread-safe tenant context is cleared after request processing.
        """
        if hasattr(request, "_tenant_context_token"):
            clear_current_tenant(request._tenant_context_token)
        else:
            clear_current_tenant()
        return response

    def process_exception(self, request, exception):
        """
        Ensure the thread-safe tenant context is cleared if an exception occurs.
        """
        if hasattr(request, "_tenant_context_token"):
            clear_current_tenant(request._tenant_context_token)
        else:
            clear_current_tenant()
