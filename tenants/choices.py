from django.db import models

''' this is where we will define choices for tenant_type and team_size fields in Tenant model. '''
class TenantType(models.TextChoices):

    DOCTOR = "DOCTOR", "Doctor"
    MENTOR = "MENTOR", "Mentor"
    FREELANCER = "FREELANCER", "Freelancer"
    TEACHER = "TEACHER", "Teacher"
    COMPANY = "COMPANY", "Company"


class TeamSize(models.TextChoices):

    JUST_ME = "just_me", "Just me"
    TWO_TO_FIVE = "2_5", "2–5 members"
    FIVE_TO_TEN = "5_10", "5–10 members"
    TEN_TO_TWENTYFIVE = "10_25", "10–25 members"
    TWENTYFIVE_PLUS = "25_plus", "25+ members"

class TenantMemberRole(models.TextChoices):

    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    PROFESSIONAL = "PROFESSIONAL", "professional"
