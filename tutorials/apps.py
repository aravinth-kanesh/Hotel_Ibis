from django.apps import AppConfig


class TutorialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tutorials'

    def ready(self):
        import tutorials.signals