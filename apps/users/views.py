"""
User views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.users.models import CustomUser
from core.serializers import UserSerializer
from core.tasks import recompute_user_eligibility

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'is_active_user']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['assigned_tasks_count', 'experience_years', 'created_at']
    
    def get_queryset(self):
        """Filter queryset based on permissions."""
        # TODO: Add role-based permissions
        return CustomUser.objects.all()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request, pk=None):
        """Update user profile and recompute eligibility."""
        user = self.get_object()
        
        # Check permission
        if request.user.id != user.id and not request.user.is_staff:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Trigger eligibility recomputation
            recompute_user_eligibility.delay(user.id)
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
