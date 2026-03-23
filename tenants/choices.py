from django.db import models




class TemplateType(models.TextChoices):
    MENTOR = "MENTOR", "Mentor"
    FITNESS = "FITNESS", "Fitness"
    TEACHER = "TEACHER", "Teacher"
    CONSULTANT = "CONSULTANT", "Consultant"

class TeamSize(models.TextChoices):
    JUST_ME = "JUST_ME", "Just Me"
    SMALL = "SMALL", "Small (2-10)"
    MEDIUM = "MEDIUM", "Medium (11-50)"
    LARGE = "LARGE", "Large (51-200)"
    ENTERPRISE = "ENTERPRISE", "Enterprise (200+)"


class TenantMemberRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    PROFESSIONAL = "PROFESSIONAL", "Professional"