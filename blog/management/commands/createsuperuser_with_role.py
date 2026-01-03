"""
Custom management command to create superuser with role
Usage: python manage.py createsuperuser_with_role
"""
from django.core.management.base import BaseCommand
from blog.models import User


class Command(BaseCommand):
    help = 'Create a superuser with role assignment'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username')
        parser.add_argument('--email', type=str, help='Email')
        parser.add_argument('--password', type=str, help='Password')
        parser.add_argument('--role', type=str, default='Admin', choices=['Admin', 'Writer', 'Reader'],
                           help='User role (default: Admin)')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        role = options.get('role', 'Admin')

        if not username:
            username = input('Username: ')
        if not email:
            email = input('Email (optional): ') or f"{username}@example.com"
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match!'))
                return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User "{username}" already exists!'))
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            is_staff=True,
            is_superuser=True
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {role} superuser: {username}'
        ))

