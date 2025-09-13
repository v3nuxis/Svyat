from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from food.models import Dish, Restaurant

User = get_user_model()


class DishesAPITestCase(TestCase):
    # def tearDown(self) -> None:
    #     return super().tearDown()

    def setUp(self) -> None:
        self.anonymous = APIClient()
        self.client = APIClient()

        self.john = User.objects.create_user(email="john@email.com", password="@Dm1n#LKJ")
        self.john.is_active = True
        self.john.save()

        # JWT Token claim
        response = self.client.post(
            reverse("obtain_token"),
            {
                "email": "john@email.com",
                "password": "@Dm1n#LKJ",
            },
        )

        # breakpoint()  # TODO: remove
        assert response.status_code == status.HTTP_200_OK, response.json()
        token = response.data["access"]

        # set the JWT token in the Authorization HTTP Header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Populate Data
        self.rest1 = Restaurant.objects.create(name="Pizza Hut", address="123 Main St")
        self.rest2 = Restaurant.objects.create(name="Dominos", address="456 Elm St")

        self.dish1 = Dish.objects.create(restaurant=self.rest1, name="Dish 1", price=100)
        self.dish2 = Dish.objects.create(restaurant=self.rest1, name="Dish 2", price=150)

        self.dish3 = Dish.objects.create(restaurant=self.rest2, name="Dish 3", price=200)
        self.dish4 = Dish.objects.create(restaurant=self.rest2, name="Dish 4", price=250)

    def test_get_dishes_NOT_authorized(self):
        response = self.anonymous.get(reverse("food-dishes-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert type(response.json()) is not list

    def test_get_dishes_authorized(self):
        response = self.client.get(reverse("food-dishes-list"))
        restarants = response.json()

        total_restaurants = len(restarants)
        total_dishes = 0
        for rest in restarants:
            total_dishes += len(rest["dishes"])

        assert response.status_code == status.HTTP_200_OK
        assert total_restaurants == 2
        assert total_dishes == 4