from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer, UserSerializer
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema

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

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    # remove lock symbol in Swagger
    @swagger_auto_schema(security=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')   # 👈 use email explicitly
    password = request.data.get('password')

    user = authenticate(username=email, password=password)  # 👈 authenticate by email
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response({'error': 'Invalid credentials'}, status=400)

@api_view(['GET'])
def profile_view(request):
    return Response(UserSerializer(request.user).data)

