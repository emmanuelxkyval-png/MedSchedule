from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create an admin superuser account'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email address')
        parser.add_argument('--password', type=str, help='Admin password')
        parser.add_argument('--phone', type=str, help='Admin phone number in format +234XXXXXXXXXX')

    def handle(self, *args, **options):
        username = options.get('username') or os.getenv('ADMIN_USERNAME', 'admin')
        email = options.get('email') or os.getenv('ADMIN_EMAIL', 'admin@medschedule.com')
        password = options.get('password') or os.getenv('ADMIN_PASSWORD', 'AdminPassword123!')
        phone = options.get('phone') or os.getenv('ADMIN_PHONE', '+2348000000000')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists."))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            phone=phone,
            role='admin'
        )
        self.stdout.write(self.style.SUCCESS(f"Successfully created admin account '{username}'!"))
