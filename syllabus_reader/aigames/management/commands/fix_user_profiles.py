from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from aigames.models import UserProfile

class Command(BaseCommand):
    help = 'Fix user profiles - create missing ones and remove duplicates'

    def handle(self, *args, **options):
        self.stdout.write('Checking user profiles...')
        
        # Find users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            created_count += 1
            self.stdout.write(f'Created profile for user: {user.username}')
        
        # Find and remove duplicate profiles (keep the first one)
        duplicate_count = 0
        for user in User.objects.all():
            profiles = UserProfile.objects.filter(user=user)
            if profiles.count() > 1:
                # Keep the first profile, delete the rest
                profiles_to_delete = profiles[1:]
                for profile in profiles_to_delete:
                    profile.delete()
                    duplicate_count += 1
                self.stdout.write(f'Removed duplicate profile(s) for user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Profile fix complete. Created {created_count} profiles, '
                f'removed {duplicate_count} duplicates.'
            )
        )
