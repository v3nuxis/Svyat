import pytest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from rest_framework import status


User = get_user_model()


@pytest.mark.django_db  # to work with database
def test_john_creation(client: Client):
    request_body = {
        "email": "john@email.com",
        "password": "@Dm1n#LKJ",
        "phone_number": "...",
        "first_name": "John",
        "last_name": "Doe",
    }
    response = client.post(path="/users/", data=request_body)
    resp = response.json()
    john = User.objects.get(id=resp["id"])

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == 1
    assert john.first_name == resp["first_name"]
    assert john.last_name == resp["last_name"]