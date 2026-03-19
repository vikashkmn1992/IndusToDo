"""
Serializers for API endpoints.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tasks.models import Task, TaskAssignment
from apps.rules.models import AssignmentRule, RuleExecutionLog
from apps.users.models import CustomUser

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'department', 'experience_years', 'location', 'bio',
            'assigned_tasks_count', 'is_active_user', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'assigned_tasks_count']


class UserSignupSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'department', 'experience_years', 'location', 'password', 'password_confirm'
        ]
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class AssignmentRuleSerializer(serializers.ModelSerializer):
    """Serializer for assignment rules."""
    class Meta:
        model = AssignmentRule
        fields = [
            'id', 'task', 'department_filter', 'min_experience_years',
            'max_experience_years', 'location_filter', 'max_assigned_tasks',
            'assignment_strategy', 'max_assignees', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for task assignments."""
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = TaskAssignment
        fields = ['id', 'task', 'assigned_to', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with rules."""
    assignment_rule = AssignmentRuleSerializer(required=False)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'due_date', 'assignment_rule']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        rule_data = validated_data.pop('assignment_rule', None)
        task = Task.objects.create(**validated_data)
        
        if rule_data:
            rule_data['task'] = task
            AssignmentRule.objects.create(**rule_data)
        
        return task


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tasks."""
    created_by = UserSerializer(read_only=True)
    assignments = TaskAssignmentSerializer(many=True, read_only=True)
    assignment_rule = AssignmentRuleSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'due_date',
            'created_by', 'created_at', 'updated_at', 'assignments', 'assignment_rule'
        ]


class TaskListSerializer(serializers.ModelSerializer):
    """List serializer for tasks."""
    created_by = serializers.StringRelatedField(read_only=True)
    assignment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date',
            'created_by', 'assignment_count', 'created_at'
        ]
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()


class RuleExecutionLogSerializer(serializers.ModelSerializer):
    """Serializer for rule execution logs."""
    class Meta:
        model = RuleExecutionLog
        fields = [
            'id', 'task', 'rule', 'status', 'eligible_users_count',
            'assigned_users_count', 'error_message', 'execution_time_ms', 'created_at'
        ]
        read_only_fields = fields
