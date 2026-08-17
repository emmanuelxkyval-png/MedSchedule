from django.db import models
from django.conf import settings

SLOT_DURATION_CHOICES = [
    (15, '15 minutes'),
    (30, '30 minutes'),
    (45, '45 minutes'),
    (60, '1 hour'),
    (90, '1.5 hours'),
    (120, '2 hours'),
]

DAY_CHOICES = [
    ('Mon', 'Monday'),
    ('Tue', 'Tuesday'),
    ('Wed', 'Wednesday'),
    ('Thu', 'Thursday'),
    ('Fri', 'Friday'),
    ('Sat', 'Saturday'),
]

SLOT_TYPE_CHOICES_BY_ROLE = {
    'doctor': [
        ('general', 'General Consultation'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
    ],
    'nurse': [
        ('dressing', 'Dressing'),
        ('injection', 'Injection'),
        ('bp_check', 'BP Check'),
        ('general', 'General'),
    ],
    'pharmacist': [
        ('prescription', 'Prescription Pickup'),
        ('counseling', 'Drug Counseling'),
    ],
    'lab_scientist': [
        ('blood_test', 'Blood Test'),
        ('urine_test', 'Urine Test'),
        ('culture', 'Culture'),
        ('other', 'Other Test'),
    ],
    'radiologist': [
        ('xray', 'X-Ray'),
        ('mri', 'MRI'),
        ('ct_scan', 'CT Scan'),
        ('ultrasound', 'Ultrasound'),
    ],
    'physiotherapist': [
        ('assessment', 'Initial Assessment'),
        ('treatment', 'Treatment Session'),
        ('review', 'Review'),
    ],
    'dentist': [
        ('checkup', 'Checkup'),
        ('cleaning', 'Cleaning'),
        ('extraction', 'Extraction'),
        ('root_canal', 'Root Canal'),
        ('filling', 'Filling'),
    ],
    'surgeon': [
        ('preop', 'Pre-op Consultation'),
        ('postop', 'Post-op Review'),
    ],
    'anesthetist': [
        ('preop_assessment', 'Pre-op Assessment'),
        ('postop_review', 'Post-op Review'),
    ],
    'dietitian': [
        ('initial', 'Initial Consultation'),
        ('followup', 'Follow-up'),
        ('diet_review', 'Diet Review'),
    ],
}

ALL_SLOT_TYPES = []
seen = set()
for types in SLOT_TYPE_CHOICES_BY_ROLE.values():
    for code, label in types:
        if code not in seen:
            ALL_SLOT_TYPES.append((code, label))
            seen.add(code)

MANUAL_CONFIRM_ROLES = ['surgeon', 'anesthetist']


class StaffAvailability(models.Model):
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(
        choices=SLOT_DURATION_CHOICES,
        default=30
    )
    max_patients = models.IntegerField(default=8)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['staff', 'day']
        ordering = ['day']

    def __str__(self):
        return f"{self.staff.get_full_name() or self.staff.username} — {self.get_day_display()} {self.start_time}-{self.end_time}"

    def get_slot_type_choices(self):
        role = self.staff.role
        return SLOT_TYPE_CHOICES_BY_ROLE.get(role, [('general', 'General')])


class BreakTime(models.Model):
    availability = models.ForeignKey(
        StaffAvailability,
        on_delete=models.CASCADE,
        related_name='breaks'
    )
    break_start = models.TimeField()
    break_end = models.TimeField()
    label = models.CharField(
        max_length=50,
        default='Break',
        help_text="e.g. Lunch, Prayer, Rest"
    )

    def __str__(self):
        return f"{self.label}: {self.break_start}–{self.break_end}"


class AppointmentSlot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
        ('break', 'Break'),
        ('completed', 'Completed'),
    ]

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_type = models.CharField(
        max_length=50,
        choices=ALL_SLOT_TYPES,
        default='general'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slot'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']

    def __str__(self):
        return f"{self.staff.get_full_name() or self.staff.username} — {self.date} {self.start_time} ({self.status})"

    def is_manual_confirm(self):
        return self.staff.role in MANUAL_CONFIRM_ROLES