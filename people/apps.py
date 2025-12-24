from django.apps import AppConfig


class PeopleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'people'
    
    def ready(self):
        """Import signals when app is ready."""
        import people.signals  # noqa