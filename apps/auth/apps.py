"""
Auth app configuration.
"""
from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth'
    
    def ready(self):
        # Setup any signals here if needed
        pass
