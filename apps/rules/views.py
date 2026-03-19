"""
Rules views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.rules.models import AssignmentRule, RuleExecutionLog
from apps.tasks.models import Task
from core.serializers import AssignmentRuleSerializer, RuleExecutionLogSerializer
from core.tasks import assign_task_to_users
from django.core.cache import cache


class AssignmentRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assignment rules.
    """
    queryset = AssignmentRule.objects.all()
    serializer_class = AssignmentRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create new assignment rule."""
        # TODO: Add permission check (admin only)
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update rule and recompute task assignments."""
        rule = self.get_object()
        task_id = rule.task_id
        
        response = super().update(request, *args, **kwargs)
        
        # Invalidate cache
        cache.delete(f"eligible_users_task_{task_id}")
        
        # Trigger reassignment with new rules
        assign_task_to_users.delay(task_id)
        
        return response
    
    @action(detail=True, methods=['get'])
    def execution_logs(self, request, pk=None):
        """Get execution logs for a rule."""
        rule = self.get_object()
        logs = RuleExecutionLog.objects.filter(rule=rule).order_by('-created_at')[:50]
        serializer = RuleExecutionLogSerializer(logs, many=True)
        return Response(serializer.data)


class RuleExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing rule execution logs (read-only).
    """
    queryset = RuleExecutionLog.objects.all().order_by('-created_at')
    serializer_class = RuleExecutionLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['task', 'status']
    ordering = ['-created_at']
