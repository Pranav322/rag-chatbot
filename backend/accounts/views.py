"""
Authentication views for registration.
Login is handled by simplejwt's TokenObtainPairView.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from adrf.views import APIView
from asgiref.sync import sync_to_async

from accounts.serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """
    User registration endpoint.
    
    POST /api/auth/register
    {
        "email": "user@example.com",
        "password": "securepass123",
        "confirm_password": "securepass123"
    }
    """
    permission_classes = [AllowAny]
    
    async def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        # Wrap validation and save in sync_to_async
        is_valid = await sync_to_async(serializer.is_valid)()
        
        if is_valid:
            user = await sync_to_async(serializer.save)()
            user_data = await sync_to_async(lambda: UserSerializer(user).data)()
            
            return Response(
                {
                    "message": "Registration successful",
                    "user": user_data
                },
                status=status.HTTP_201_CREATED
            )
        
        errors = await sync_to_async(lambda: serializer.errors)()
        return Response(
            {"error": "Registration failed", "detail": errors},
            status=status.HTTP_400_BAD_REQUEST
        )
