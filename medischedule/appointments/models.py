from django.db import models
from django.conf import settings
from accounts.models import CLINICAL_ROLES as CLINICAL_STAFF, NON_CLINICAL_ROLES

NON_CLINICAL_STAFF = NON_CLINICAL_ROLES + ['admin']

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    TYPE_CHOICES = [
        ('patient_clinical', 'Patient Appointment'),
        ('staff_meeting', 'Staff Meeting'),
        ('manager_meeting', 'Manager Called Meeting'),
    ]

    appointment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='patient_clinical'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        null=True, blank=True
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        null=True, blank=True
    )
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.appointment_type == 'manager_meeting':
            return f"Manager Meeting on {self.date} at {self.time}"
        return f"{self.patient} → {self.doctor} on {self.date} at {self.time}"