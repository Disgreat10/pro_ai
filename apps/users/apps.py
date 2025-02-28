from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        This ensures that the signal handlers are connected when Django starts.
        """
        import apps.users.signals  # noqa
