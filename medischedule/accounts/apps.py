from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_admin(sender, **kwargs):
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@medschedule.com',
                password='AdminPassword123!',
                phone='+2348000000000',
                role='admin'
            )
            print("Default admin account 'admin' created successfully!")
    except Exception as e:
        print(f"Admin auto-creation check note: {e}")

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
