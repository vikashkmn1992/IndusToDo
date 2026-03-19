"""
Core models and utilities.
"""
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model with common fields."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
