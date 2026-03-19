"""
Authentication views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.serializers import UserSerializer, UserSignupSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with user info."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view."""
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """User signup endpoint."""
    if request.method == 'POST':
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'User created successfully', 'user': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
