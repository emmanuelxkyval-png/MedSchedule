from django.contrib import admin
from .models import StaffAvailability, BreakTime, AppointmentSlot


@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['staff', 'day', 'start_time', 'end_time', 'slot_duration', 'max_patients', 'is_active']
    list_filter = ['day', 'is_active']
    search_fields = ['staff__username', 'staff__first_name', 'staff__last_name']


@admin.register(BreakTime)
class BreakTimeAdmin(admin.ModelAdmin):
    list_display = ['availability', 'label', 'break_start', 'break_end']


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'start_time', 'end_time', 'status', 'slot_type']
    list_filter = ['status', 'date']
    search_fields = ['staff__username']