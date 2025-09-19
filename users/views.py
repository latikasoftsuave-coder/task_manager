from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()

# -------- REGISTER --------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(security=[])   # 🔓 removes lock in Swagger
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "message": "User registered successfully. Use /api/auth/login/ to get JWT."
        }, status=status.HTTP_201_CREATED)


# -------- LOGIN (JWT) --------
class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(security=[])   # 🔓 removes lock in Swagger
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# -------- PROFILE --------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    return Response(UserSerializer(request.user).data)
