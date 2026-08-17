from django.core.management.base import BaseCommand
from accounts.models import User
from schedules.utils import generate_slots_for_staff


class Command(BaseCommand):
    help = 'Generate appointment slots for all active clinical staff'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days ahead to generate slots for'
        )

    def handle(self, *args, **kwargs):
        days = kwargs['days']
        from accounts.models import CLINICAL_ROLES
        staff_members = User.objects.filter(role__in=CLINICAL_ROLES)
        total_created = 0

        for staff in staff_members:
            count = generate_slots_for_staff(staff, days_ahead=days)
            total_created += count
            if count > 0:
                self.stdout.write(
                    f'Generated {count} slots for '
                    f'{staff.get_full_name() or staff.username}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {total_created} total slots '
                f'for {staff_members.count()} staff members'
            )
        )