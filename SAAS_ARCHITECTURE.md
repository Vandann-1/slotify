# Slotify Multi-Tenant SaaS Architecture Guide

Welcome to the Slotify SaaS architecture guide! This document explains how multi-tenancy is structured across the codebase and outlines guidelines for developers creating new features (such as booking systems, chat channels, and custom client modules).

---

## Architecture Overview

Slotify uses a **Shared Database, Row-Level Isolation** multi-tenancy model. 
This means all tenants (workspaces) share the same PostgreSQL/SQLite database, and records are isolated from each other via a foreign key reference to the `Tenant` model.

### Key Components

1. **`TenantContext` (`tenants/context.py`)**: A thread-safe, `contextvars`-based context holder. It stores the currently active tenant for the duration of a request.
2. **`TenantMiddleware` (`tenants/middleware.py`)**: Automatically inspects incoming HTTP requests. It resolves the active workspace using the following priorities:
   - `X-Tenant-Slug` or `X-Workspace-Slug` HTTP Headers.
   - `workspace_slug` or `tenant_slug` query parameters.
   - Host Subdomain (e.g. `workspace-slug.slotify.com`).
   - Fallback to the authenticated user's default/first workspace.
3. **`TenantAwareModel` (`tenants/models/base.py`)**: An abstract base model that automatically adds a `tenant` foreign key to subclasses, overrides the default manager to filter by the current `TenantContext`, and auto-injects the current tenant during `.save()`.
4. **DRF Permissions (`tenants/permissions.py`)**:
   - `IsTenantMember`: Confirms the user has an active membership in the request's workspace.
   - `IsTenantAdmin`: Confirms the user has an Admin or Owner role in the request's workspace.

---

## How to Build New Features

### 1. Creating a Tenant-Aware Model

Any model containing tenant-specific user data **must** inherit from `TenantAwareModel`.

```python
from django.db import models
from tenants.models import TenantAwareModel

class Booking(TenantAwareModel):
    client_name = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Booking for {self.client_name} (Tenant: {self.tenant})"
```

#### What this automatically gives you:
- **Automatic Field Injection**: Adds a `tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)` field.
- **Default Query Isolation**: `Booking.objects.all()` automatically returns bookings only for the active workspace in the request.
- **Auto-populating Saves**: Saving `Booking(client_name="John")` will auto-link the active tenant from context.
- **Administrative Escape Hatch**: Use `Booking.unfiltered_objects.all()` to access all records regardless of the active tenant context.

---

### 2. Writing Tenant-Aware Views

When using Django Rest Framework (DRF) ViewSets, specify the tenant permission classes to secure endpoints:

```python
from rest_framework import viewsets
from tenants.permissions import IsTenantMember, IsTenantAdmin
from .models import Booking
from .serializers import BookingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsTenantMember]  # Ensures user belongs to the active tenant

    def get_queryset(self):
        # Even if you use Booking.objects.all(), it is automatically filtered by tenant!
        return Booking.objects.all()
```

---

### 3. Testing Tenant Isolation

Always write tests that verify one workspace cannot fetch or write to another workspace's records.

Example pattern:
```python
from django.test import TestCase
from tenants.models import Tenant
from tenants.context import set_current_tenant, clear_current_tenant
from .models import Booking

class TenantIsolationTestCase(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a")
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b")

    def test_query_isolation(self):
        # Set context to Tenant A
        set_current_tenant(self.tenant_a)
        Booking.objects.create(client_name="Client of A")

        # Set context to Tenant B
        set_current_tenant(self.tenant_b)
        Booking.objects.create(client_name="Client of B")

        # Queries under Tenant B context only show Tenant B bookings
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.first().client_name, "Client of B")

        clear_current_tenant()
```
