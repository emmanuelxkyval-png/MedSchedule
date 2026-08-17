from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from notifications.utils import notify_account_created


class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="First Name"
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        label="Last Name"
    )
    email = forms.EmailField(
        required=True,
        label="Email Address"
    )
    phone = forms.CharField(
        max_length=14,
        required=True,
        label="Phone Number",
        help_text="Format: +2348101010101"
    )
    gender = forms.ChoiceField(
        choices=[
            ('', '-- Select Gender --'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        required=True,
        label="Gender"
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        label="Hospital Role"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username',
            'email', 'phone', 'gender',
            'date_of_birth', 'role',
            'password1', 'password2'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "This phone number is already registered."
            )
        return phone


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm

    list_display = ['username', 'get_full_name', 'email', 'role', 'phone', 'gender']
    list_filter = ['role', 'gender']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            notify_account_created(obj)

    add_fieldsets = (
        ('Login Details', {
            'fields': ('username', 'password1', 'password2')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'email',
                'phone', 'gender', 'date_of_birth'
            )
        }),
        ('Hospital Role', {
            'fields': ('role',),
        }),
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Personal Info Extra', {
            'fields': ('phone', 'gender', 'date_of_birth', 'address')
        }),
        ('Hospital Role', {
            'fields': ('role',),
        }),
    )


admin.site.unregister(Group)
admin.site.site_header = "MediSchedule Administration"
admin.site.site_title = "MediSchedule Admin"
admin.site.index_title = "Hospital Management Panel"