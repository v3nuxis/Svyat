from django.urls import path
from .views import DishesListGroupedView, DishCreateView, OrderCreateView

urlpatterns = [
    path('dishes', DishesListGroupedView.as_view(), name='dishes-grouped'),
    path('dishes/create', DishCreateView.as_view(), name='dish-create'),
    path('orders', OrderCreateView.as_view(), name='order-create'),
]