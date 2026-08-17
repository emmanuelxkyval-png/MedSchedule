from django import forms
from .models import StaffAvailability, BreakTime, SLOT_DURATION_CHOICES, DAY_CHOICES

TW = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300'
TW_SELECT = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white'


class StaffAvailabilityForm(forms.ModelForm):
    class Meta:
        model = StaffAvailability
        fields = [
            'day', 'start_time', 'end_time',
            'slot_duration', 'max_patients', 'is_active'
        ]
        widgets = {
            'day': forms.Select(attrs={'class': TW_SELECT}),
            'start_time': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'slot_duration': forms.Select(attrs={'class': TW_SELECT}),
            'max_patients': forms.NumberInput(attrs={'class': TW, 'min': 1, 'max': 50}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError(
                "End time must be after start time."
            )
        return cleaned_data


class BreakTimeForm(forms.ModelForm):
    class Meta:
        model = BreakTime
        fields = ['break_start', 'break_end', 'label']
        widgets = {
            'break_start': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'label': forms.TextInput(attrs={
                'class': TW,
                'placeholder': 'e.g. Lunch, Prayer, Rest'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('break_start')
        end = cleaned_data.get('break_end')
        if start and end and start >= end:
            raise forms.ValidationError(
                "Break end time must be after break start time."
            )
        return cleaned_data