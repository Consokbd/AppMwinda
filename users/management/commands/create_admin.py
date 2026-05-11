from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update admin user for AppMwinda'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin username (default: admin)')
        parser.add_argument('--email', type=str, default='admin@appmwinda.com', help='Admin email')
        parser.add_argument('--password', type=str, default='Admin@123456', help='Admin password')
        parser.add_argument('--role', type=str, default='admin', help='Admin role (default: admin)')
        parser.add_argument('--direction', type=str, default='design', help='Admin direction (default: design)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        role = options['role']
        direction = options['direction']

        try:
            # Check if user exists
            user = User.objects.filter(username=username).first()
            
            if user:
                # Update existing user - make sure password is set correctly
                user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.role = role
                user.direction = direction
                user.set_password(password)  # Use set_password to hash the password
                user.save()
                self.stdout.write(self.style.SUCCESS('[OK] Updated admin user "{}"'.format(username)))
            else:
                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    direction=direction,
                )
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS('[OK] Created admin user "{}"'.format(username)))
            
            # Verify password works
            from django.contrib.auth import authenticate
            test_auth = authenticate(username=username, password=password)
            if test_auth:
                self.stdout.write(self.style.SUCCESS('[OK] Password verified - authentication works'))
            else:
                self.stdout.write(self.style.WARNING('[WARNING] Password verification failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('[ERROR] Failed to create admin: {}'.format(str(e))))

        self.stdout.write(self.style.SUCCESS('\n[OK] Admin credentials:'))
        self.stdout.write('  Username: {}'.format(username))
        self.stdout.write('  Password: {}'.format(password))
        self.stdout.write('  Email: {}'.format(email))
        self.stdout.write('  Role: {}'.format(role))
        self.stdout.write('  Direction: {}'.format(direction))
