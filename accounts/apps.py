from django.apps import AppConfig
import threading

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        try:
            from services.mongodb import seed_initial_data_if_empty
            # Run seeding in background thread so Gunicorn boots instantly (< 0.1s)
            threading.Thread(target=seed_initial_data_if_empty, daemon=True).start()
        except Exception:
            pass
