"""
Rules app configuration.
"""
from django.apps import AppConfig


class RulesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rules'
    
    def ready(self):
        # Setup any signals here if needed
        pass
