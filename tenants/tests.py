from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, connection
from django.contrib.auth.models import AnonymousUser

from tenants.models import Tenant, TenantMember, TenantAwareTestModel
from tenants.choices import TenantMemberRole, TemplateType
from tenants.context import set_current_tenant, get_current_tenant, clear_current_tenant
from tenants.middleware import TenantMiddleware
from Backend.permissions import IsTenantMember, IsTenantAdmin

User = get_user_model()


class TenantContextTestCase(TestCase):
    """
    Verifies that the thread-safe contextvars context functions correctly.
    """
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.tenant = Tenant.objects.create(name="Acme Corp", slug="acme", owner=self.user)

    def tearDown(self):
        clear_current_tenant()

    def test_context_set_get_clear(self):
        self.assertIsNone(get_current_tenant())
        token = set_current_tenant(self.tenant)
        self.assertEqual(get_current_tenant(), self.tenant)
        clear_current_tenant(token)
        self.assertIsNone(get_current_tenant())


class TenantAwareModelTestCase(TestCase):
    """
    Verifies automatic query filtering and tenant validation for TenantAwareModel.
    """
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a", owner=self.user)
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b", owner=self.user)

    def tearDown(self):
        clear_current_tenant()

    def test_save_without_tenant_context_raises_error(self):
        # Saving without context should raise validation error if tenant isn't manually assigned
        obj = TenantAwareTestModel(name="Test")
        with self.assertRaises(ValidationError):
            obj.save()

    def test_save_with_manual_tenant(self):
        # Manually assigned tenant should succeed
        obj = TenantAwareTestModel(name="Test", tenant=self.tenant_a)
        obj.save()
        self.assertEqual(obj.tenant, self.tenant_a)

    def test_save_with_context_auto_populates(self):
        # Set tenant context and save
        set_current_tenant(self.tenant_a)
        obj = TenantAwareTestModel(name="Test")
        obj.save()
        self.assertEqual(obj.tenant, self.tenant_a)

    def test_query_isolation_by_tenant(self):
        # Save records under Tenant A
        set_current_tenant(self.tenant_a)
        TenantAwareTestModel.objects.create(name="A1")
        TenantAwareTestModel.objects.create(name="A2")

        # Save record under Tenant B
        set_current_tenant(self.tenant_b)
        TenantAwareTestModel.objects.create(name="B1")

        # Query while in Tenant B context
        self.assertEqual(TenantAwareTestModel.objects.count(), 1)
        self.assertEqual(TenantAwareTestModel.objects.first().name, "B1")

        # Query while in Tenant A context
        set_current_tenant(self.tenant_a)
        self.assertEqual(TenantAwareTestModel.objects.count(), 2)

        # Query unfiltered escape hatch
        self.assertEqual(TenantAwareTestModel.unfiltered_objects.count(), 3)



class TenantMiddlewareTestCase(TestCase):
    """
    Verifies that TenantMiddleware correctly parses slugs from HTTP headers and binds context.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.tenant = Tenant.objects.create(name="Acme", slug="acme", owner=self.user)

    def tearDown(self):
        clear_current_tenant()

    def test_resolves_tenant_from_header(self):
        middleware = TenantMiddleware(lambda req: None)
        request = self.factory.get("/", HTTP_X_TENANT_SLUG="acme")
        request.user = AnonymousUser()

        middleware.process_request(request)
        self.assertEqual(request.tenant, self.tenant)
        self.assertEqual(get_current_tenant(), self.tenant)


class DRFPermissionsTestCase(TestCase):
    """
    Verifies that DRF permission classes protect tenant endpoints correctly.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.intruder = User.objects.create_user(username="intruder", password="password")

        self.tenant = Tenant.objects.create(name="Acme", slug="acme", owner=self.user)
        # Create user memberships
        self.member_ship = TenantMember.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantMemberRole.OWNER
        )

    def test_is_tenant_member_permission(self):
        permission = IsTenantMember()

        # Authorized member
        request = self.factory.get("/")
        request.user = self.user
        request.tenant = self.tenant
        request.tenant_member = self.member_ship
        self.assertTrue(permission.has_permission(request, None))

        # Intruder (not member)
        request_intruder = self.factory.get("/")
        request_intruder.user = self.intruder
        request_intruder.tenant = self.tenant
        request_intruder.tenant_member = None
        self.assertFalse(permission.has_permission(request_intruder, None))

    def test_is_tenant_admin_permission(self):
        permission = IsTenantAdmin()

        # Owner/Admin member
        request = self.factory.get("/")
        request.user = self.user
        request.tenant = self.tenant
        request.tenant_member = self.member_ship
        self.assertTrue(permission.has_permission(request, None))

        # Change role to professional (non-admin)
        self.member_ship.role = TenantMemberRole.PROFESSIONAL
        self.member_ship.save()

        request_non_admin = self.factory.get("/")
        request_non_admin.user = self.user
        request_non_admin.tenant = self.tenant
        request_non_admin.tenant_member = self.member_ship
        self.assertFalse(permission.has_permission(request_non_admin, None))
