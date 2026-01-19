from django.apps import AppConfig


class AiAgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agents'

    def ready(self):
        # Importujemy sygnały, aby zadziałały dekoratory @receiver
        import ai_agents.signals
