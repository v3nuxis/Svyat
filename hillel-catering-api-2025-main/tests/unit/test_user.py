import pytest
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserTestCase(TestCase):
    def test_john_creation(self):
        # setup input data
        payload = {
            "email": "john@email.com",
            "phone_number": "+38067..",
            "password": "@Dm1n#LKJ",
            "first_name": "John",
            "last_name": "Doe",
        }

        # action
        User.objects.create(**payload)

        # evaluate
        john = User.objects.first()
        total_users = User.objects.count()

        assert total_users == 1
        assert john.role == "customer"
        for attr, value in payload.items():
            if attr == "password":
                continue

            assert getattr(john, attr) == value


@pytest.mark.parametrize(
    "payload",
    [
        {
            "email": "john@email.com",  # same email
            "password": "password",
            "phone_number": "+380000",
        },
        {
            "email": "marry@email.com",
            "password": "password",
            "phone_number": "+3809611",  # same phone number
        },
    ],
)
def test_user_duplicate(john, django_user_model, payload):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            django_user_model.objects.create_user(**payload)