#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laurel.settings.local')
django.setup()

from apps.user.models import User

# Create superuser
email = 'admin@estimation.com'
password = 'admin123'

if not User.objects.filter(email=email).exists():
    user = User.objects.create_superuser(
        username='admin',
        email=email,
        password=password,
        first_name='Admin',
        last_name='User',
    )
    print(f'Superuser created successfully!')
    print(f'Email: {email}')
    print(f'Password: {password}')
else:
    print('Superuser already exists!')
