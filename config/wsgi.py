import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

# Fail-safe automatic migration on server startup
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception:
    pass
