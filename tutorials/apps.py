from django.apps import AppConfig

# Configuration for the tutorials app, sets the default auto field and app name.
class TutorialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tutorials'

    # The method is called when the app is ready. Imports the signals module.
    def ready(self):
        import tutorials.signals