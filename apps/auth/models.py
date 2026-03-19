"""
Authentication models.
"""
from django.db import models
from apps.core.models import BaseModel


class RevokedToken(BaseModel):
    """Revoked JWT tokens (for logout)."""
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    token_type = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'revoked_token'
