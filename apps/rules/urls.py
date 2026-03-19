"""
Rules URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssignmentRuleViewSet, RuleExecutionLogViewSet

app_name = 'rules'

router = DefaultRouter()
router.register(r'assignment-rules', AssignmentRuleViewSet)
router.register(r'execution-logs', RuleExecutionLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
