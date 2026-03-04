from django.db import models


class WorkspaceType(models.TextChoices):
    SOLO = "SOLO", "Solo"
    TEAM = "TEAM", "Team"


class TenantType(models.TextChoices):
    DOCTOR = "DOCTOR", "Doctor"
    MENTOR = "MENTOR", "Mentor"
    FREELANCER = "FREELANCER", "Freelancer"
    TEACHER = "TEACHER", "Teacher"
    COMPANY = "COMPANY", "Company"


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