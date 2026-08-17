from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time, timedelta
from unittest.mock import patch

from accounts.models import User
from schedules.models import AppointmentSlot, StaffAvailability
from schedules.utils import get_available_slots, get_available_dates
from medischedule.error_handlers import PermissionDeniedError

class SchedulesTests(TestCase):
    def setUp(self):
        # Create users
        self.doctor = User.objects.create_user(
            username='doctor1',
            password='password123',
            role='doctor',
            phone='+2348012345678'
        )
        self.patient = User.objects.create_user(
            username='patient1',
            password='password123',
            role='patient',
            phone='+2348087654321'
        )
        self.it_staff = User.objects.create_user(
            username='it1',
            password='password123',
            role='it_staff',
            phone='+2348000000000'
        )

    def test_get_available_slots_filters_past_today(self):
        """Test that get_available_slots only returns future slots for today, and all slots for tomorrow."""
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        # Create slots for today: one past (10:00 AM), one future (4:00 PM) relative to a simulated 12:00 PM now.
        slot_past = AppointmentSlot.objects.create(
            staff=self.doctor,
            date=today,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )
        slot_future = AppointmentSlot.objects.create(
            staff=self.doctor,
            date=today,
            start_time=time(16, 0),
            end_time=time(16, 30),
            status='available'
        )
        slot_tomorrow = AppointmentSlot.objects.create(
            staff=self.doctor,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )

        # Mock timezone.now() to be today at 12:00 PM (Lagos time)
        lagos_tz = timezone.get_current_timezone()
        mocked_now = datetime.combine(today, time(12, 0))
        mocked_now = timezone.make_aware(mocked_now, lagos_tz)

        with patch('django.utils.timezone.now', return_value=mocked_now):
            # Test today's slots (only future slot should be returned)
            today_slots = get_available_slots(self.doctor, today)
            self.assertEqual(today_slots.count(), 1)
            self.assertEqual(today_slots.first(), slot_future)

            # Test tomorrow's slots (all slots should be returned regardless of time)
            tomorrow_slots = get_available_slots(self.doctor, tomorrow)
            self.assertEqual(tomorrow_slots.count(), 1)
            self.assertEqual(tomorrow_slots.first(), slot_tomorrow)

    def test_get_available_dates(self):
        """Test that get_available_dates correctly returns list of dates with available slots."""
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        # Past slot for today
        AppointmentSlot.objects.create(
            staff=self.doctor,
            date=today,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )
        # Future slot for tomorrow
        AppointmentSlot.objects.create(
            staff=self.doctor,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )

        # Mock timezone.now() to be today at 12:00 PM (Lagos time)
        lagos_tz = timezone.get_current_timezone()
        mocked_now = datetime.combine(today, time(12, 0))
        mocked_now = timezone.make_aware(mocked_now, lagos_tz)

        with patch('django.utils.timezone.now', return_value=mocked_now):
            # Since today only has a past slot, only tomorrow should show up in available dates
            dates = get_available_dates(self.doctor)
            self.assertEqual(dates, [tomorrow])

            # Now add a future slot for today
            AppointmentSlot.objects.create(
                staff=self.doctor,
                date=today,
                start_time=time(16, 0),
                end_time=time(16, 30),
                status='available'
            )
            # Now both today and tomorrow should be returned
            dates = get_available_dates(self.doctor)
            self.assertEqual(dates, [today, tomorrow])

    def test_error_handling_middleware_html(self):
        """Test that the global error handling middleware handles PermissionDeniedError on HTML requests via flash message and redirect."""
        client = Client()
        client.login(username='it1', password='password123')

        # IT staff accessing schedule_home should raise PermissionDeniedError
        response = client.get(reverse('schedule_home'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify the flash message error is present
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Only clinical staff can access schedules.")

    def test_error_handling_middleware_ajax(self):
        """Test that the global error handling middleware handles AJAX/JSON requests and returns a structured JSON error response."""
        client = Client()
        client.login(username='it1', password='password123')

        # Make an AJAX request
        response = client.get(
            reverse('schedule_home'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {
            'success': False,
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': 'Only clinical staff can access schedules.'
            }
        })
