"""
Task models.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Task(BaseModel):
    """Task model with assignment rules."""
    STATUS_CHOICES = [
        ('Todo', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
    ]
    
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Todo', db_index=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, db_index=True)
    due_date = models.DateTimeField(db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    
    class Meta:
        db_table = 'task'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]

    def __str__(self):
        return self.title


class TaskAssignment(BaseModel):
    """Assignment of a task to a user."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    
    class Meta:
        db_table = 'task_assignment'
        unique_together = ('task', 'assigned_to')
        indexes = [
            models.Index(fields=['assigned_to', 'task']),
            models.Index(fields=['task', 'created_at']),
        ]

    def __str__(self):
        return f"{self.task.title} -> {self.assigned_to.username}"
