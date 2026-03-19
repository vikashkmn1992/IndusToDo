"""
Task views with high-performance APIs.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Q, Prefetch, Count
from django.core.cache import cache
from apps.tasks.models import Task, TaskAssignment
from apps.rules.models import AssignmentRule
from core.serializers import (
    TaskDetailSerializer, TaskListSerializer, TaskCreateSerializer,
    TaskAssignmentSerializer, RuleExecutionLogSerializer
)
from core.tasks import assign_task_to_users
import json


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for task management.
    - Create tasks with dynamic rules
    - View eligible tasks
    - Perform CRUD operations
    """
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action in ['list', 'my_eligible_tasks']:
            return TaskListSerializer
        return TaskDetailSerializer
    
    def get_queryset(self):
        """Optimized queryset with prefetch_related."""
        queryset = Task.objects.select_related('created_by').prefetch_related(
            'assignments', 'assignment_rule'
        ).all()
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create task with rules."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set created_by to current user
        task = serializer.save(created_by=request.user)
        
        # Trigger background task assignment
        assign_task_to_users.delay(task.id)
        
        return Response(
            TaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_eligible_tasks(self, request):
        """
        Get tasks eligible for current user.
        
        Performance: Cached for 5 minutes, uses database indexes.
        """
        user_id = request.user.id
        cache_key = f"eligible_tasks_user_{user_id}"
        
        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        try:
            # Get all task assignments for current user
            eligible_tasks = Task.objects.filter(
                assignments__assigned_to__id=user_id
            ).select_related('created_by').prefetch_related(
                'assignment_rule'
            ).distinct().values(
                'id', 'title', 'status', 'priority', 'due_date',
                'created_by__username', 'created_at'
            )
            
            eligible_tasks_list = list(eligible_tasks)
            
            # Cache for 5 minutes
            cache.set(cache_key, {
                'count': len(eligible_tasks_list),
                'tasks': eligible_tasks_list
            }, 300)
            
            return Response({
                'count': len(eligible_tasks_list),
                'tasks': eligible_tasks_list
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def eligible_users(self, request, pk=None):
        """
        Get list of eligible users for a task.
        
        Performance: Cached and optimized with indexes.
        """
        cache_key = f"eligible_users_task_{pk}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        try:
            task = self.get_object()
            rule = AssignmentRule.objects.get(task=task)
            
            # Get current assignments
            assigned_users = TaskAssignment.objects.filter(
                task=task
            ).values_list('assigned_to', flat=True)
            
            from core.rule_engine import RuleEngine
            engine = RuleEngine()
            eligible_users = engine.get_eligible_users(rule)
            
            eligible_data = [
                {
                    'id': u.id,
                    'username': u.username,
                    'department': u.department,
                    'experience_years': u.experience_years,
                    'assigned_tasks_count': u.assigned_tasks_count,
                    'is_assigned': u.id in assigned_users
                }
                for u in eligible_users
            ]
            
            response_data = {
                'task_id': task.id,
                'eligible_count': len(eligible_data),
                'assigned_count': len(assigned_users),
                'users': eligible_data
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, response_data, 600)
            
            return Response(response_data)
            
        except AssignmentRule.DoesNotExist:
            return Response(
                {'error': 'No assignment rule found for this task'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def recompute_eligibility(self, request):
        """
        Recompute eligibility for all tasks or a specific task.
        """
        task_id = request.data.get('task_id')
        
        from core.rule_engine import RuleEngine
        engine = RuleEngine()
        
        if task_id:
            result = engine.recompute_task_eligibility(task_id)
        else:
            # Recompute all
            result = {'status': 'recomputation_queued'}
            from core.tasks import recompute_all_eligibilities
            recompute_all_eligibilities.delay()
        
        return Response(result)
