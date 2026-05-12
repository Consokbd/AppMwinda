import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppMwinda.settings')
import django
django.setup()
from django.test import Client

c = Client()
r = c.post('/login/?next=/', {'username': 'test', 'password': 'test123'})
print('status', r.status_code)
print('url', getattr(r, 'url', None))
print('content', r.content[:500])
