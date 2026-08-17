from django import forms
from .models import PatientProfile
from accounts.models import User

TW = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300'
TW_SELECT = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white'


class PersonalInfoForm(forms.ModelForm):
    """Form for updating personal info from the User model."""
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': 'Last name'})
    )
    phone = forms.CharField(
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': '+2348101010101'})
    )
    gender = forms.ChoiceField(
        choices=[
            ('', '-- Select Gender --'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': TW_SELECT})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': TW, 'type': 'date'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TW, 'rows': 2,
            'placeholder': 'Your home address'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'gender', 'date_of_birth', 'address']


class MedicalProfileForm(forms.ModelForm):
    """Form for medical information."""
    class Meta:
        model = PatientProfile
        fields = [
            'blood_group', 'genotype',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'allergies',
            'current_medications',
            'chronic_conditions',
            'medical_history',
        ]
        widgets = {
            'blood_group': forms.Select(attrs={'class': TW_SELECT}),
            'genotype': forms.Select(attrs={'class': TW_SELECT}),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': TW, 'placeholder': 'e.g. Jane Smith'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': TW, 'placeholder': '+2348101010101'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': TW, 'placeholder': 'e.g. Mother, Spouse, Brother'
            }),
            'allergies': forms.Textarea(attrs={
                'class': TW, 'rows': 2,
                'placeholder': 'e.g. Penicillin, Peanuts, None'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': TW, 'rows': 2,
                'placeholder': 'List any medications you are currently taking'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'class': TW, 'rows': 2,
                'placeholder': 'e.g. Diabetes, Hypertension, Asthma, None'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': TW, 'rows': 3,
                'placeholder': 'Any past surgeries, major illnesses or hospitalizations'
            }),
        }
        labels = {
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_phone': 'Emergency Contact Phone',
            'emergency_contact_relationship': 'Relationship to You',
            'allergies': 'Known Allergies',
            'current_medications': 'Current Medications',
            'chronic_conditions': 'Chronic Conditions',
            'medical_history': 'Medical History',
        }