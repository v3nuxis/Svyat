from typing import Any
from rest_framework.views import APIView
from rest_framework import status
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import permissions, routers, serializers, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.conf import settings
from .models import User
from .services import ActivationService
from .tasks import send_activation_email


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "password",
            "role",
        ]

    def validate(self, attrs: dict[str, Any]):
        """Change the password for its hash to make Token-based authentication available."""

        attrs["password"] = make_password(attrs["password"])
        attrs["is_active"] = False

        return super().validate(attrs=attrs)


class UserActivationSerializer(serializers.Serializer):
    key = serializers.UUIDField()


class UsersAPIViewSet(viewsets.GenericViewSet):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action == "activate":
            return [permissions.AllowAny()]
        else:
            return [permissions.IsAuthenticated()]

    def list(self, request: Request):
        return Response(UserSerializer(request.user).data, status=200)

    def create(self, request: Request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Activation process
        activation_service = ActivationService(
            email=getattr(serializer.instance, "email")
        )
        activation_key = activation_service.create_activation_key()
        activation_service.save_activation_information(
            user_id=getattr(serializer.instance, "id"),
            activation_key=activation_key,
        )
        activation_service.send_user_activation_email(activation_key=activation_key)

        return Response(UserSerializer(serializer.instance).data, status=201)
    

    @action(methods=["POST"], detail=False)
    def activate(self, request: Request) -> Response:
        serializer = UserActivationSerializer(data=request.data)
        serializer.is_valid()

        activation_service = ActivationService()
        try:
            activation_service.activate_user(
                activation_key=serializer.validated_data["key"]
            )
        except ValueError as error:
            raise ValidationError("Activation link expired") from error

        return Response(data=None, status=204)
    
    
    
    @action(methods=["POST"], detail=False)
    def resend_activation_link(self, email: str, request: Request) -> None:
        email = request.data.get('email')
        
        if not email:
            raise ValidationError("Email is required")
        
        activation_service = ActivationService()
        try:
            activation_service.send_user_activation_link(email=email)
        except ValueError:
            pass
        
        return Response(
            data={"message": "Activation link sent successfully"},
            status = status.HTTP_200_OK
        )
            
        # try:
        #     User = User.objects.get(email=email)
        # except User.DoesNotExist:
        #     raise ValueError("User with this email does not exist")
        
        # activation_key= self.create_activation_key()
        # self.save_information(user_id=user.id, activation_key=activation_key)
        # self.email = email
        # self.send_user_activation_email(activation_key=activation_key)
        
        
router = routers.DefaultRouter()
router.register(r"", UsersAPIViewSet, basename="user")
