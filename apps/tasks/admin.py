"""
Django admin configuration.
"""
from django.contrib import admin
from apps.users.models import CustomUser
from apps.tasks.models import Task, TaskAssignment
from apps.rules.models import AssignmentRule, RuleExecutionLog


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'department', 'experience_years', 'assigned_tasks_count']
    list_filter = ['department', 'is_active_user', 'created_at']
    search_fields = ['username', 'email', 'location']
    ordering = ['-created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'due_date', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'assigned_to', 'created_at']
    list_filter = ['created_at']
    search_fields = ['task__title', 'assigned_to__username']


@admin.register(AssignmentRule)
class AssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ['task', 'assignment_strategy', 'max_assigned_tasks', 'is_active']
    list_filter = ['is_active', 'assignment_strategy', 'created_at']
    search_fields = ['task__title']


@admin.register(RuleExecutionLog)
class RuleExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'status', 'eligible_users_count', 'assigned_users_count', 'execution_time_ms', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['task__title']
    ordering = ['-created_at']
