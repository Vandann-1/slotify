from django.db import models
from django.utils import timezone
from tenants.models.tenant import Tenant


class Plans(models.Model):

    BILLING_CYCLE = (
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    price = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE,
        default="monthly"
    )

    member_limit = models.IntegerField(default=3)
    booking_limit = models.IntegerField(default=100)

    description = models.TextField(blank=True)
    features = models.JSONField(default=list, blank=True)

    razorpay_plan_id = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"
    
    
class Addon(models.Model):

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.name    
    

class Subscription(models.Model):

    STATUS_CHOICES = (
        ("active", "Active"),
        ("trial", "Trial"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    )

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="subscription"
    )

    plan = models.ForeignKey(
        Plans,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscriptions"
    )

    addons = models.ManyToManyField(
        Addon,
        blank=True,
        related_name="subscriptions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    razorpay_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    start_date = models.DateField(default=timezone.now)

    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"{self.tenant.name} - {plan_name}"    