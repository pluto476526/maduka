from django.apps import AppConfig


class KonnektConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konnekt'

    def ready(self):
        import konnekt.signals
