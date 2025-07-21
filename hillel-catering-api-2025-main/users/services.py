import uuid
from shared.cache import CacheService

from django.core.mail import send_mail
from .models import User


class ActivationService:
    UUID_NAMESPACE = uuid.uuid4()

    def __init__(self, email: str | None = None):
        self.email: str | None = email
        self.cache: CacheService = CacheService()

    def create_activation_key(self):
        # whether:
        # key = uuid.uuid3(self.UUID_NAMESPACE, self.email)
        # or
        return uuid.uuid4()

    def save_activation_information(self, user_id: int, activation_key: str):
        """Save activation data to the cache.
        1. Connect to the Cache Service
        2. Save structure to the Cache:
        {
            "0a33d01f-b18f-4369-abd2-e85002f24846": {
                "user_id": 3
            }
        }
        3. Return `None`
        """

        self.cache.set(
            namespace="activation",
            key=activation_key,
            value={"user_id": user_id},
            ttl=800,
        )

        return None

    def send_user_activation_email(self, activation_key: str):
        if self.email is None:
            raise ValueError(f"No email specified for user activation process")

        # SMTP Client Send Email Request
        activation_link = f"https://frontend.catering.com/activation/{activation_key}"
        send_mail(
            subject="User Activation",
            message=f"Please, activate your account: {activation_link}",
            from_email="admin@catering.com",
            recipient_list=[self.email],
        )

    def activate_user(self, activation_key: str) -> None:
        user_cache_payload: dict | None = self.cache.get(
            namespace="activation",
            key=activation_key,
        )

        if user_cache_payload is None:
            raise ValueError("No payload in cache")

        user = User.objects.get(id=user_cache_payload["user_id"])
        user.is_active = True
        user.save()

        # or for instance:
        # User.objects.filter(id=user...).update(is_active=True)

    def resend_activation_link(self, email: str) -> None:
        """Send user activation link to specified email."""

        raise NotImplementedError
