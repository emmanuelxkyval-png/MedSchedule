from django import forms
from .models import Appointment
from accounts.models import User, CLINICAL_ROLES as CLINICAL_STAFF, NON_CLINICAL_ROLES
from schedules.models import AppointmentSlot, SLOT_TYPE_CHOICES_BY_ROLE
from schedules.utils import get_available_dates
from datetime import date, timedelta
from django.utils import timezone
NON_CLINICAL_STAFF = NON_CLINICAL_ROLES + ['admin']

TW = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300'
TW_SELECT = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white'


class PatientAppointmentForm(forms.Form):
    staff = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=CLINICAL_STAFF),
        label="Select Staff",
        empty_label="Select an Available Staff Member",
        widget=forms.Select(attrs={'class': TW_SELECT, 'id': 'staff-select'})
    )
    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={
            'class': TW,
            'type': 'date',
            'id': 'date-select',
            'min': str(timezone.localdate())
        })
    )
    slot = forms.ModelChoiceField(
        queryset=AppointmentSlot.objects.none(),
        label="Select Time Slot",
        empty_label="Select an Available Slot",
        widget=forms.Select(attrs={'class': TW_SELECT, 'id': 'slot-select'})
    )
    reason = forms.CharField(
        required=False,
        label="Reason for Visit",
        widget=forms.Textarea(attrs={
            'class': TW,
            'rows': 3,
            'placeholder': 'Describe your reason for visit...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'staff' in self.data and 'date' in self.data:
            try:
                from datetime import datetime
                staff_id = int(self.data.get('staff'))
                date_str = self.data.get('date')
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                self.fields['slot'].queryset = AppointmentSlot.objects.filter(
                    staff_id=staff_id,
                    date=target_date,
                    status='available'
                ).order_by('start_time')
            except (ValueError, TypeError):
                pass


class StaffAppointmentForm(forms.Form):
    staff = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role__in=CLINICAL_STAFF + [
                'receptionist', 'admin_staff',
                'it_staff', 'manager', 'admin'
            ]
        ),
        label="Select Staff Member",
        empty_label="Select a Staff Member",
        widget=forms.Select(attrs={'class': TW_SELECT})
    )
    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={
            'class': TW,
            'type': 'date',
            'min': str(timezone.localdate())
        })
    )
    time = forms.TimeField(
        label="Select Time",
        widget=forms.TimeInput(attrs={'class': TW, 'type': 'time'})
    )
    reason = forms.CharField(
        required=False,
        label="Reason for Meeting",
        widget=forms.Textarea(attrs={
            'class': TW,
            'rows': 3,
            'placeholder': 'Reason for meeting...'
        })
    )

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if current_user:
            self.fields['staff'].queryset = self.fields['staff'].queryset.exclude(id=current_user.id)


class ManagerMeetingForm(forms.Form):
    meeting_title = forms.CharField(
        max_length=200,
        required=True,
        label="Meeting Title",
        help_text="e.g. Monthly Staff Review",
        widget=forms.TextInput(attrs={
            'class': TW,
            'placeholder': 'e.g. Monthly Staff Review'
        })
    )
    date = forms.DateField(
        label="Meeting Date",
        widget=forms.DateInput(attrs={
            'class': TW,
            'type': 'date',
            'min': str(timezone.localdate())
        })
    )
    time = forms.TimeField(
        label="Meeting Time",
        widget=forms.TimeInput(attrs={'class': TW, 'type': 'time'})
    )
    reason = forms.CharField(
        required=False,
        label="Meeting Agenda",
        widget=forms.Textarea(attrs={
            'class': TW,
            'rows': 3,
            'placeholder': 'Meeting agenda...'
        })
    )