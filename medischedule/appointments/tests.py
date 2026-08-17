from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from appointments.forms import StaffAppointmentForm

class AppointmentSelfBookingTests(TestCase):
    def setUp(self):
        # Create clinical staff users
        self.doctor1 = User.objects.create_user(
            username='doctor1',
            password='password123',
            role='doctor',
            phone='+2348012345678'
        )
        self.doctor2 = User.objects.create_user(
            username='doctor2',
            password='password123',
            role='doctor',
            phone='+2348012345679'
        )
        self.nurse = User.objects.create_user(
            username='nurse1',
            password='password123',
            role='nurse',
            phone='+2348012345680'
        )

    def test_staff_appointment_form_excludes_self(self):
        """Test that StaffAppointmentForm excludes the current logged-in staff member from staff choices."""
        # If doctor1 is current_user, doctor1 should not be in the queryset but doctor2 and nurse should.
        form = StaffAppointmentForm(current_user=self.doctor1)
        queryset = form.fields['staff'].queryset
        self.assertNotIn(self.doctor1, queryset)
        self.assertIn(self.doctor2, queryset)
        self.assertIn(self.nurse, queryset)

        # If doctor2 is current_user, doctor2 should not be in the queryset but doctor1 and nurse should.
        form2 = StaffAppointmentForm(current_user=self.doctor2)
        queryset2 = form2.fields['staff'].queryset
        self.assertNotIn(self.doctor2, queryset2)
        self.assertIn(self.doctor1, queryset2)
        self.assertIn(self.nurse, queryset2)

    def test_staff_appointment_form_without_current_user(self):
        """Test that StaffAppointmentForm does not exclude any staff members if current_user is not provided."""
        form = StaffAppointmentForm()
        queryset = form.fields['staff'].queryset
        self.assertIn(self.doctor1, queryset)
        self.assertIn(self.doctor2, queryset)
        self.assertIn(self.nurse, queryset)

    def test_book_appointment_view_excludes_self_in_form(self):
        """Test that the book appointment view renders the form excluding the current user."""
        client = Client()
        client.login(username='doctor1', password='password123')
        response = client.get(reverse('book_appointment'))
        self.assertEqual(response.status_code, 200)
        # Check that the form in context has the queryset excluding doctor1
        form = response.context['form']
        self.assertIsInstance(form, StaffAppointmentForm)
        self.assertNotIn(self.doctor1, form.fields['staff'].queryset)
