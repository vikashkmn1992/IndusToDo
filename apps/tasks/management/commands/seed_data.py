"""
Management command to seed initial data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tasks.models import Task
from apps.rules.models import AssignmentRule
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        # Create test users
        users_data = [
            {'username': 'admin', 'first_name': 'Admin', 'department': 'IT', 'experience_years': 10},
            {'username': 'alice', 'first_name': 'Alice', 'department': 'Finance', 'experience_years': 5},
            {'username': 'bob', 'first_name': 'Bob', 'department': 'HR', 'experience_years': 3},
            {'username': 'charlie', 'first_name': 'Charlie', 'department': 'IT', 'experience_years': 7},
            {'username': 'diana', 'first_name': 'Diana', 'department': 'Operations', 'experience_years': 4},
            {'username': 'eve', 'first_name': 'Eve', 'department': 'Finance', 'experience_years': 6},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'email': f"{user_data['username']}@example.com",
                    'department': user_data['department'],
                    'experience_years': user_data['experience_years'],
                    'location': random.choice(['NYC', 'LA', 'Chicago', 'Boston']),
                    'is_active_user': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"Created user: {user.username}")
            users.append(user)
        
        # Create sample tasks
        task_data = [
            {'title': 'Implement authentication', 'description': 'Add JWT auth', 'priority': 3},
            {'title': 'API optimization', 'description': 'Optimize endpoints', 'priority': 2},
            {'title': 'Database indexing', 'description': 'Add indexes', 'priority': 3},
            {'title': 'Write tests', 'description': 'Unit and integration tests', 'priority': 2},
            {'title': 'Documentation', 'description': 'API documentation', 'priority': 1},
        ]
        
        for task_info in task_data:
            task, created = Task.objects.get_or_create(
                title=task_info['title'],
                defaults={
                    'description': task_info['description'],
                    'priority': task_info['priority'],
                    'status': 'Todo',
                    'due_date': timezone.now() + timedelta(days=random.randint(1, 30)),
                    'created_by': users[0],  # Admin
                }
            )
            if created:
                self.stdout.write(f"Created task: {task.title}")
                
                # Create assignment rules
                rule_configs = [
                    {
                        'department_filter': ['IT', 'Finance'],
                        'min_experience_years': 4,
                        'max_assigned_tasks': 5,
                        'assignment_strategy': 'least_loaded',
                    },
                    {
                        'department_filter': ['Operations', 'HR'],
                        'min_experience_years': 3,
                        'max_assigned_tasks': 4,
                        'assignment_strategy': 'random',
                    },
                ]
                
                rule_config = random.choice(rule_configs)
                rule, _ = AssignmentRule.objects.get_or_create(
                    task=task,
                    defaults=rule_config
                )
                self.stdout.write(f"Created rule for task: {task.title}")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
