from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema

from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer, UserSerializer


# -------- REGISTER --------
class RegisterView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @swagger_auto_schema(security=[])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "message": "User registered successfully. Use /api/auth/login/ to get JWT.",
            },
            status=status.HTTP_201_CREATED,
        )


# -------- LOGIN --------
class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(security=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# -------- PROFILE --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    return Response(UserSerializer(request.user).data)
