from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User

phone_validator = RegexValidator(
    regex=r'^\+234\d{10}$',
    message="Format: +234XXXXXXXXXX — must be exactly 10 digits after +234"
)

TW = 'w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300'

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': 'John'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': 'Smith'})
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': TW, 'placeholder': 'john@email.com'})
    )
    phone = forms.CharField(
        max_length=14,
        validators=[phone_validator],
        required=True,
        label="Phone Number",
        help_text="Format: +2348101010101",
        widget=forms.TextInput(attrs={'class': TW, 'placeholder': '+2348101010101'})
    )
    gender = forms.ChoiceField(
        choices=[
            ('', '-- Select Gender --'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        required=True,
        label="Gender",
        widget=forms.Select(attrs={'class': TW})
    )
    date_of_birth = forms.DateField(
        required=True,
        label="Date of Birth",
        widget=forms.DateInput(attrs={'class': TW, 'type': 'date'})
    )
    address = forms.CharField(
        required=False,
        label="Home Address",
        widget=forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'Your home address'})
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username',
            'email', 'phone', 'gender',
            'date_of_birth', 'address',
            'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': TW, 'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': TW, 'placeholder': 'Create a password'}
        )
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': TW, 'placeholder': 'Confirm your password'}
        )
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email address is already registered."
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "This phone number is already registered."
            )
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        if commit:
            user.save()
        return user