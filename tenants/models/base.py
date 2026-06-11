from django.db import models
from django.core.exceptions import ValidationError
from tenants.models.tenant import Tenant
from tenants.context import get_current_tenant


class TenantQuerySet(models.QuerySet):
    """
    QuerySet that provides tenant-filtering functionality.
    """
    def filter_by_current_tenant(self):
        tenant = get_current_tenant()
        if tenant:
            return self.filter(tenant=tenant)
        return self


class TenantManager(models.Manager):
    """
    Manager that automatically restricts queries to the active tenant context.
    """
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).filter_by_current_tenant()


class TenantAwareModel(models.Model):
    """
    Abstract base model that enforces row-level tenant isolation.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="%(class)s_set"
    )

    # The default manager is tenant-aware
    objects = TenantManager()
    
    # Escape hatch manager for administrative or cross-tenant operations
    unfiltered_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auto-inject tenant from context if not already set
        if not hasattr(self, "tenant") or self.tenant is None:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValidationError("A tenant context is required to save a TenantAwareModel.")
        
        super().save(*args, **kwargs)


class TenantAwareTestModel(TenantAwareModel):
    """
    A concrete implementation of TenantAwareModel used solely for testing isolation and context behavior.
    """
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "tenants_test_aware_model"

