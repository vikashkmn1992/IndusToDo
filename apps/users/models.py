"""
User models.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.core.models import BaseModel


class CustomUser(AbstractUser):
    """Extended user model with additional fields."""
    DEPARTMENT_CHOICES = [
        ('Finance', 'Finance'),
        ('HR', 'HR'),
        ('IT', 'IT'),
        ('Operations', 'Operations'),
    ]
    
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, db_index=True)
    experience_years = models.IntegerField(default=0, db_index=True)
    location = models.CharField(max_length=100, db_index=True)
    bio = models.TextField(blank=True, null=True)
    is_active_user = models.BooleanField(default=True, db_index=True)
    
    # Performance optimization: cache current assigned tasks count
    assigned_tasks_count = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        db_table = 'custom_user'
        indexes = [
            models.Index(fields=['department', 'experience_years']),
            models.Index(fields=['is_active_user', 'assigned_tasks_count']),
            models.Index(fields=['department', 'location']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
