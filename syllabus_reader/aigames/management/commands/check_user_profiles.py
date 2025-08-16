from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from aigames.models import UserProfile

class Command(BaseCommand):
    help = 'Check user profile status'

    def handle(self, *args, **options):
        self.stdout.write('Checking user profile status...')
        
        for user in User.objects.all():
            profiles = UserProfile.objects.filter(user=user)
            if profiles.count() > 1:
                self.stdout.write(f"❌ User {user.username} has {profiles.count()} profiles")
            elif profiles.count() == 0:
                self.stdout.write(f"⚠️  User {user.username} has no profile")
            else:
                self.stdout.write(f"✅ User {user.username} - OK")
        
        self.stdout.write(f"\\nTotal users: {User.objects.count()}")
        self.stdout.write(f"Total profiles: {UserProfile.objects.count()}")
        
        # Try creating a test user to see the error
        self.stdout.write("\\nTesting user creation...")
        try:
            test_user = User.objects.create_user(username='test_user_temp', password='testpass')
            self.stdout.write(f"✅ Test user created successfully: {test_user.username}")
            
            # Check if profile was created
            if hasattr(test_user, 'profile'):
                self.stdout.write(f"✅ Profile created for test user")
            else:
                self.stdout.write(f"⚠️  No profile created for test user")
            
            # Clean up
            test_user.delete()
            self.stdout.write("🗑️ Test user deleted")
            
        except Exception as e:
            self.stdout.write(f"❌ Error creating test user: {e}")
