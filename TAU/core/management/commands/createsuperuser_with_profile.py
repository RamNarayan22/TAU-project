from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from core.models import Profile, Department

class Command(BaseCommand):
    help = 'Create a superuser with a profile or update existing superuser profile'

    def handle(self, *args, **options):
        # Check for existing superuser
        existing_superuser = User.objects.filter(is_superuser=True).first()
        
        if existing_superuser:
            self.stdout.write(self.style.WARNING(f'Superuser {existing_superuser.username} already exists'))
            update = input('Do you want to update their profile? (y/n): ')
            if update.lower() == 'y':
                try:
                    # Create or update profile
                    profile, created = Profile.objects.get_or_create(
                        user=existing_superuser,
                        defaults={
                            'is_admin': True,
                            'must_change_password': True
                        }
                    )
                    if not created:
                        profile.is_admin = True
                        profile.must_change_password = True
                        profile.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'Profile updated for superuser {existing_superuser.username}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error updating profile: {str(e)}'))
            return

        # Create new superuser if none exists
        username = input('Username: ')
        email = input('Email: ')
        password = input('Password: ')

        try:
            # Create superuser
            superuser = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

            # Create profile for superuser
            Profile.objects.create(
                user=superuser,
                is_admin=True,
                must_change_password=True
            )

            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}')) 