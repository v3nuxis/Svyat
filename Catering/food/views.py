from rest_framework import generics, permissions
from .models import Dish, Restaurant, Order
from .serializiers import (
    DishSerializer,
    RestaurantWithDishesSerializer,
    OrderCreateSerializer
)
from .permissions import IsAdminUserRole

class DishesListGroupedView(generics.ListAPIView):
    queryset = Restaurant.objects.prefetch_related('dishes').all()
    serializer_class = RestaurantWithDishesSerializer
    permission_classes = [permissions.AllowAny]

class DishCreateView(generics.CreateAPIView):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = [IsAdminUserRole]

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)