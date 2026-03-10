from django.db import models
from tenants.models.tenant import Tenant
from django.utils import timezone
# Create your models here.

class Plans(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=11,decimal_places=2,default=0)
    member_limit = models.IntegerField(default=3)
    
    booking_limit = models.IntegerField(default=100)
    
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    
    razorpay_plan_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name



class Addon (models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=11,decimal_places=2,default=0)
    description = models.TextField(blank=True)  
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name



class Subscription(models.Model):
    plan = models.ForeignKey(Plans, on_delete=models.SET_NULL, null =True)
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="subscription"
    )
    
    addons = models.ManyToManyField(Addon, blank=True)
    
    razorpay_subscription_id = models.CharField(max_length=255,blank=True, null = True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"{self.tenant.name} - {plan_name}"    