from django.db.models.signals import post_save
from django.dispatch import receiver
from tenants.models.tenant import Tenant
from .models import Subscription, Plans



''' tis signal creates a default subscription for a tenant when a new tenant is created.
The default subscription is set to the "Free" plan. '''

@receiver(post_save, sender=Tenant)
def create_default_subscription(sender, instance, created, **kwargs):

    if created:
        free_plan = Plans.objects.filter(name="Free").first()

        Subscription.objects.create(
            tenant=instance,
            plan=free_plan
        )