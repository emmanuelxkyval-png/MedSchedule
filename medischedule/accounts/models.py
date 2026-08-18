from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+234\d{10}$',
    message="Phone number must be in format: +234XXXXXXXXXX (10 digits after +234)"
)

CLINICAL_ROLES = [
    'doctor', 'nurse', 'pharmacist', 'lab_scientist',
    'radiologist', 'physiotherapist', 'dentist',
    'surgeon', 'anesthetist', 'dietitian'
]

SCHEDULE_ROLES = CLINICAL_ROLES + ['receptionist']

NON_CLINICAL_ROLES = ['it_staff', 'admin_staff']

class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('pharmacist', 'Pharmacist'),
        ('lab_scientist', 'Laboratory Scientist'),
        ('radiologist', 'Radiologist'),
        ('physiotherapist', 'Physiotherapist'),
        ('dentist', 'Dentist'),
        ('surgeon', 'Surgeon'),
        ('anesthetist', 'Anesthetist'),
        ('dietitian', 'Dietitian'),
        ('receptionist', 'Receptionist'),
        ('admin_staff', 'Administrative Staff'),
        ('it_staff', 'IT Staff'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='patient'
    )
    phone = models.CharField(
        max_length=14,
        validators=[phone_validator],
        unique=True,
        blank=False
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)

    REQUIRED_FIELDS = ['email', 'phone']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_staff_member(self):
        return self.role not in ['patient']