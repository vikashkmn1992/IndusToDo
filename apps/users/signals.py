"""
Signals for automatic handling of user changes.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.users.models import CustomUser
from core.tasks import recompute_user_eligibility


@receiver(post_save, sender=CustomUser)
def on_user_updated(sender, instance, created, update_fields, **kwargs):
    """
    Trigger eligibility recomputation when user attributes change.
    """
    if not created and update_fields:
        # Check if any profile attributes changed
        profile_fields = {
            'department', 'experience_years', 'location',
            'is_active_user', 'assigned_tasks_count'
        }
        
        if profile_fields & set(update_fields):
            # Async task to recompute eligibility
            recompute_user_eligibility.delay(instance.id)
