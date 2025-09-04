from django.core.management.base import BaseCommand
from myapp.models import User  # Import your custom User model
from django.db.models import Q

class Command(BaseCommand):
    help = 'Change user role from user to operator'

    def handle(self, *args, **kwargs):
        # Fetch all users with the role 'user'
        users_to_update = User.objects.filter(role='user')  # Assuming your role field is named 'role'
        
        if not users_to_update:
            self.stdout.write(self.style.WARNING('No users found with role "user".'))
            return

        for user in users_to_update:
            # Change role from 'user' to 'operator'
            user.role = 'operator'
            user.save()  # Save the user with the updated role

            self.stdout.write(self.style.SUCCESS(f'User "{user.username}" role successfully changed to "operator"'))