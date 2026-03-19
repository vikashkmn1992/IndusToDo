"""
Celery tasks for background processing.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import F, Count
from apps.tasks.models import Task, TaskAssignment
from apps.rules.models import AssignmentRule
from apps.users.models import CustomUser
from core.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def assign_task_to_users(self, task_id: int):
    """
    Background task to assign a task to eligible users.
    Triggered when a task is created or when rules change.
    """
    try:
        task = Task.objects.get(id=task_id)
        rule = AssignmentRule.objects.get(task=task)
        
        engine = RuleEngine()
        eligible_count, assigned_count, status = engine.assign_task(task, rule)
        
        logger.info(
            f"Task {task_id} assigned to {assigned_count} users "
            f"out of {eligible_count} eligible"
        )
        
        return {
            'task_id': task_id,
            'eligible_count': eligible_count,
            'assigned_count': assigned_count,
            'status': status
        }
        
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return {'error': f'Task {task_id} not found'}
    except AssignmentRule.DoesNotExist:
        logger.error(f"No rules for task {task_id}")
        return {'error': f'No rules for task {task_id}'}
    except Exception as exc:
        logger.error(f"Error in assign_task_to_users: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def recompute_user_eligibility(self, user_id: int):
    """
    Background task to recompute task eligibility when user attributes change.
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Get all active rules
        rules = AssignmentRule.objects.filter(is_active=True)
        
        engine = RuleEngine()
        recomputed_count = 0
        
        for rule in rules:
            # Check if user meets criteria
            eligible_users = engine.get_eligible_users(rule)
            user_is_eligible = user in eligible_users
            
            # Check if user already has this assignment
            has_assignment = TaskAssignment.objects.filter(
                task=rule.task,
                assigned_to=user
            ).exists()
            
            # Add or remove assignment as needed
            if user_is_eligible and not has_assignment:
                TaskAssignment.objects.create(task=rule.task, assigned_to=user)
                user.assigned_tasks_count = F('assigned_tasks_count') + 1
                recomputed_count += 1
            elif not user_is_eligible and has_assignment:
                TaskAssignment.objects.filter(
                    task=rule.task,
                    assigned_to=user
                ).delete()
                user.assigned_tasks_count = F('assigned_tasks_count') - 1
                recomputed_count += 1
        
        if recomputed_count > 0:
            user.save(update_fields=['assigned_tasks_count'])
        
        logger.info(f"Recomputed eligibility for user {user_id}, affected {recomputed_count} tasks")
        return {'user_id': user_id, 'recomputed_tasks': recomputed_count}
        
    except CustomUser.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': f'User {user_id} not found'}
    except Exception as exc:
        logger.error(f"Error in recompute_user_eligibility: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task
def recompute_all_eligibilities():
    """
    Periodic task to recompute all eligibilities (hourly or as needed).
    """
    try:
        from django.db.models import F
        
        # Reset all counts
        CustomUser.objects.all().update(assigned_tasks_count=0)
        
        # Recalculate from scratch
        assignments = TaskAssignment.objects.values('assigned_to').annotate(count=Count('id'))
        for assignment in assignments:
            CustomUser.objects.filter(id=assignment['assigned_to']).update(
                assigned_tasks_count=assignment['count']
            )
        
        logger.info("Completed full eligibility recomputation")
        return {'status': 'completed'}
        
    except Exception as e:
        logger.error(f"Error in recompute_all_eligibilities: {e}")
        return {'error': str(e)}
