from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ''' this in simple words it is the main user model'''

    full_name = models.CharField(max_length=255)



    role = models.CharField(
        max_length=10,
        blank=True,
        null=True,
    )
    
    def __str__(self):
        return self.username
    
    
    
    
class ProfessionalProfile(models.Model):
    '''this professional profile is for the professionals
    in react POST API  api/professional-profile
    
    ''' 
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="professional_profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    experience_years = models.IntegerField(blank=True, null=True)
    # profile_picture = models.URLField(blank=True, null=True)skeip for now
    
    linkdin_url = models.URLField(blank=True, null=True)
      
# -------------------------------------------------------
# these fields are for future use, to implement profile completion and verification features
# -------------------------------------------------------   
    profile_completed = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "professional_profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["verified"]),
        ]

    def __str__(self):
        return f"ProfessionalProfile({self.user})"  
