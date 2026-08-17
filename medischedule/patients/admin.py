from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'blood_group',
        'genotype',
        'emergency_contact_name',
        'emergency_contact_phone'
    ]
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name'
    ]
    list_filter = ['blood_group', 'genotype']