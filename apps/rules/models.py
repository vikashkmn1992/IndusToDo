"""
Rule engine models for task assignment.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.tasks.models import Task
import json


class AssignmentRule(BaseModel):
    """Dynamic rules for automatic task assignment."""
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='assignment_rule')
    
    # Rule conditions (stored as JSON for flexibility)
    department_filter = models.JSONField(null=True, blank=True, default=list)  # ['Finance', 'HR']
    min_experience_years = models.IntegerField(default=0, null=True, blank=True)
    max_experience_years = models.IntegerField(null=True, blank=True)
    location_filter = models.JSONField(null=True, blank=True, default=list)  # ['NYC', 'LA']
    max_assigned_tasks = models.IntegerField(default=5, db_index=True)
    
    # assignment strategy
    STRATEGY_CHOICES = [
        ('first_available', 'First Available'),
        ('least_loaded', 'Least Loaded'),
        ('round_robin', 'Round Robin'),
        ('random', 'Random'),
    ]
    assignment_strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES, default='least_loaded')
    
    # If multiple eligible users exist, how many should get the task?
    max_assignees = models.IntegerField(default=1)
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'assignment_rule'
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return f"Rules for {self.task.title}"

    def get_rule_dict(self):
        """Get rules as a dictionary."""
        return {
            'department_filter': self.department_filter or [],
            'min_experience_years': self.min_experience_years or 0,
            'max_experience_years': self.max_experience_years,
            'location_filter': self.location_filter or [],
            'max_assigned_tasks': self.max_assigned_tasks,
            'assignment_strategy': self.assignment_strategy,
            'max_assignees': self.max_assignees,
        }


class RuleExecutionLog(BaseModel):
    """Log of rule execution and task assignments."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='execution_logs')
    rule = models.ForeignKey(AssignmentRule, on_delete=models.CASCADE, related_name='execution_logs')
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    eligible_users_count = models.IntegerField(default=0)
    assigned_users_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'rule_execution_log'
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Execution log for {self.task.title} - {self.status}"
