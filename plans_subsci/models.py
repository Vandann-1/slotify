from django.db import models
from tenants.models.tenant import Tenant
from django.utils import timezone
# Create your models here.

class Plans(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=11,decimal_places=2,default=0)
    member_limit = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    isactive_plan = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name



class Subscription(models.Model):
    plan = models.ForeignKey(Plans, on_delete=models.CASCADE)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name}"    