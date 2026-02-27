''' this accounts/signals.py file is 
for creating a ProfessionalProfile 
automatically when a new User is created. '''


# accounts/signals.py


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ProfessionalProfile

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_professional_profile(sender, instance, created, **kwargs):
    if created:
        ProfessionalProfile.objects.get_or_create(user=instance)