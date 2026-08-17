from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import Appointment
from schedules.utils import mark_past_slots_completed


class Command(BaseCommand):
    help = 'Auto update appointment statuses based on date and time'

    def handle(self, *args, **kwargs):
        now = timezone.localtime(timezone.now())
        today = now.date()
        current_time = now.time()

        # Mark past confirmed appointments as completed
        # if staff didn't mark them done
        past_confirmed = Appointment.objects.filter(
            status='confirmed',
            date__lt=today
        )
        completed_count = 0
        for appt in past_confirmed:
            appt.status = 'completed'
            appt.save()
            completed_count += 1

        # Mark today's confirmed appointments as completed
        # if the time has passed by more than 2 hours
        from datetime import timedelta
        threshold_dt = now - timedelta(hours=2)

        if threshold_dt.date() == today:
            todays_past = Appointment.objects.filter(
                status='confirmed',
                date=today,
                time__lt=threshold_dt.time()
            )
            for appt in todays_past:
                appt.status = 'completed'
                appt.save()
                completed_count += 1

        # Mark past pending appointments as cancelled
        # if staff never confirmed them
        past_pending = Appointment.objects.filter(
            status='pending',
            date__lt=today
        )
        cancelled_count = 0
        for appt in past_pending:
            appt.status = 'cancelled'
            appt.save()
            cancelled_count += 1

        # Mark past slots
        slots_updated = mark_past_slots_completed()

        self.stdout.write(
            self.style.SUCCESS(
                f'Auto update complete: '
                f'{completed_count} appointments completed, '
                f'{cancelled_count} pending appointments cancelled, '
                f'{slots_updated} slots updated'
            )
        )