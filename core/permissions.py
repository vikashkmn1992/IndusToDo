"""
Permissions for role-based access control.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allow access to admin only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsManager(permissions.BasePermission):
    """Allow access to managers."""
    
    def has_permission(self, request, view):
        # TODO: Implement manager role
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access to owner or admin."""
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_staff
