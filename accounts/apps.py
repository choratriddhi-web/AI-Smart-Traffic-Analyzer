from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        try:
            from services.mongodb import seed_initial_data_if_empty
            seed_initial_data_if_empty()
        except Exception as e:
            # Prevent startup crash during migrations
            pass
