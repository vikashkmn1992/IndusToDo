"""
Rule execution engine for task assignment.
"""
import logging
from typing import List, Dict, Tuple
from django.db.models import Q, F, Count
from django.utils import timezone
from apps.users.models import CustomUser
from apps.tasks.models import Task, TaskAssignment
from apps.rules.models import AssignmentRule, RuleExecutionLog
import random
import time

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Dynamic rule-based task assignment engine.
    
    Strategies:
    - Filter eligible users based on rules
    - Assign tasks using specified strategy (first_available, least_loaded, round_robin, random)
    - Log execution for debugging
    """
    
    def __init__(self):
        self.cache_key_prefix = "eligible_users"
    
    def get_eligible_users(self, rule: AssignmentRule) -> List[CustomUser]:
        """
        Get list of users eligible for a task based on rules.
        
        Performance: O(1) for filtered query due to multi-field indexes
        """
        try:
            query = CustomUser.objects.filter(is_active_user=True)
            
            # Department filter
            if rule.department_filter:
                query = query.filter(department__in=rule.department_filter)
            
            # Experience filter
            if rule.min_experience_years is not None:
                query = query.filter(experience_years__gte=rule.min_experience_years)
            if rule.max_experience_years is not None:
                query = query.filter(experience_years__lte=rule.max_experience_years)
            
            # Location filter
            if rule.location_filter:
                query = query.filter(location__in=rule.location_filter)
            
            # Max assigned tasks filter
            query = query.filter(assigned_tasks_count__lt=rule.max_assigned_tasks)
            
            # Optimize query with select_related and only specific fields
            eligible_users = list(
                query.only('id', 'username', 'assigned_tasks_count')
                     .order_by('assigned_tasks_count')  # For least_loaded strategy
            )
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Error getting eligible users: {e}")
            return []
    
    def assign_task(self, task: Task, rule: AssignmentRule) -> Tuple[int, int, str]:
        """
        Execute rule engine to assign task to eligible users.
        
        Returns: (eligible_count, assigned_count, status_message)
        """
        start_time = time.time()
        
        try:
            eligible_users = self.get_eligible_users(rule)
            eligible_count = len(eligible_users)
            
            if eligible_count == 0:
                logger.warning(f"No eligible users found for task {task.id}")
                status = 'failed'
                error_msg = "No eligible users found matching the criteria"
                assigned_count = 0
            else:
                # Select assignees based on strategy
                assignees = self._select_assignees(eligible_users, rule)
                assigned_count = 0
                
                # Create assignments
                for user in assignees:
                    try:
                        assignment, created = TaskAssignment.objects.get_or_create(
                            task=task,
                            assigned_to=user
                        )
                        if created:
                            # Update user's assigned tasks count
                            user.assigned_tasks_count = F('assigned_tasks_count') + 1
                            user.save(update_fields=['assigned_tasks_count'])
                            assigned_count += 1
                    except Exception as e:
                        logger.error(f"Error assigning task to user {user.id}: {e}")
                
                status = 'success' if assigned_count == len(assignees) else 'partial'
                error_msg = None
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log execution
            RuleExecutionLog.objects.create(
                task=task,
                rule=rule,
                status=status,
                eligible_users_count=eligible_count,
                assigned_users_count=assigned_count,
                error_message=error_msg,
                execution_time_ms=execution_time
            )
            
            logger.info(
                f"Task {task.id} assignment: {eligible_count} eligible, "
                f"{assigned_count} assigned, {execution_time}ms"
            )
            
            return eligible_count, assigned_count, status
            
        except Exception as e:
            logger.error(f"Error in task assignment: {e}")
            
            RuleExecutionLog.objects.create(
                task=task,
                rule=rule,
                status='failed',
                eligible_users_count=0,
                assigned_users_count=0,
                error_message=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return 0, 0, 'failed'
    
    def _select_assignees(self, eligible_users: List[CustomUser], rule: AssignmentRule) -> List[CustomUser]:
        """Select assignees based on strategy."""
        if rule.assignment_strategy == 'first_available':
            return eligible_users[:rule.max_assignees]
        
        elif rule.assignment_strategy == 'least_loaded':
            # Already sorted by assigned_tasks_count in get_eligible_users
            return eligible_users[:rule.max_assignees]
        
        elif rule.assignment_strategy == 'round_robin':
            # Simple round robin: pick every nth user
            step = max(1, len(eligible_users) // rule.max_assignees)
            return eligible_users[::step][:rule.max_assignees]
        
        elif rule.assignment_strategy == 'random':
            return random.sample(eligible_users, min(rule.max_assignees, len(eligible_users)))
        
        else:
            return eligible_users[:rule.max_assignees]
    
    def recompute_task_eligibility(self, task_id: int) -> Dict:
        """Recompute eligibility for a specific task."""
        try:
            task = Task.objects.get(id=task_id)
            rule = AssignmentRule.objects.get(task=task)
            
            # Clear existing assignments
            TaskAssignment.objects.filter(task=task).delete()
            
            # Reset user counts
            CustomUser.objects.all().update(assigned_tasks_count=0)
            
            # Reassign
            eligible, assigned, status = self.assign_task(task, rule)
            
            return {
                'task_id': task_id,
                'eligible_users': eligible,
                'assigned_users': assigned,
                'status': status
            }
        except Task.DoesNotExist:
            return {'error': f'Task {task_id} not found'}
        except AssignmentRule.DoesNotExist:
            return {'error': f'No rules found for task {task_id}'}
        except Exception as e:
            logger.error(f"Error recomputing eligibility: {e}")
            return {'error': str(e)}
