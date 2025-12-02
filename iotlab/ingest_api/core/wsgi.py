import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iotlab.ingest_api.core.settings')

application = get_wsgi_application() 