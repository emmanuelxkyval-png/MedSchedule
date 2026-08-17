from django.db import models
from django.conf import settings


class PatientProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]

    GENOTYPE_CHOICES = [
        ('AA', 'AA'), ('AS', 'AS'),
        ('SS', 'SS'), ('AC', 'AC'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        blank=True
    )
    genotype = models.CharField(
        max_length=2,
        choices=GENOTYPE_CHOICES,
        blank=True
    )
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=14, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"