from .base import *
import os
#from dotenv import load_dotenv

#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#load_dotenv(dotenv_path)

# Override settings for development
DEBUG = False

ALLOWED_HOSTS = ['test-dev-eastus-webapp.azurewebsites.net','laurel-ag.biz']

CSRF_TRUSTED_ORIGINS = ['https://test-dev-eastus-webapp.azurewebsites.net','https://laurel-ag.biz']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
