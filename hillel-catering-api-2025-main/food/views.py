import io
import csv
from typing import Any
from datetime import date

from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.db import transaction
from rest_framework import permissions, routers, serializers, viewsets, generics
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.views.decorators.cache import cache_page

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.pagination import PageNumberPagination


from users.models import Role, User
from .models import Dish, Order, OrderItem, OrderStatus, Restaurant
from .enums import DeliveryProvider


class DishPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    
class DishListView(generics.ListAPIView):
    serializer_class = DishSerializer
    pagination_class = DishPagination
    permission_classes = [permissions.IsAdminUser]

def get_queryset(self):
    query_set = Dish.objects.all()
    name = self.request.query_params.get("name")
    if "name":
        query_set = query_set.filter(name_icontains=name)
    return query_set

class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        exclude = ["restaurant"]
        fiels = "__all__"


class RestaurantSerializer(serializers.ModelSerializer):
    dishes = DishSerializer(many=True)

    class Meta:
        model = Restaurant
        fields = "__all__"


class OrderItemSerializer(serializers.Serializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dish.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class OrderSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    items = OrderItemSerializer(many=True)
    eta = serializers.DateField()
    total = serializers.IntegerField(min_value=1, read_only=True)
    status = serializers.ChoiceField(OrderStatus.choices(), read_only=True)
    delivery_provider = serializers.CharField()

    @property
    def calculated_total(self) -> int:
        total = 0

        for item in self.validated_data["items"]:
            dish: Dish = item["dish"]
            quantity: int = item["quantity"]
            total += dish.price * quantity

        return total

    # validate_<any-fieldname>
    # def validate_items(self, value: date):
    #     raise ValidationError("Some error")

    def validate_eta(self, value: date):
        if (value - date.today()).days < 1:
            raise ValidationError("ETA must be min 1 day after today.")
        else:
            return value


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        assert type(request.user) == User
        user: User = request.user

        if user.role == Role.ADMIN:
            return True
        else:
            return False


class BaseFitlers:
    @staticmethod
    def camel_to_snake_case(value):
        result = []
        for char in value:
            if char.isupper():
                if result:
                    result.append("_")
                result.append(char.lower())
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def snake_to_camel_case(value):
        parts = value.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    def __init__(self, **kwargs) -> None:
        errors: dict[str, dict[str, Any]] = {"queryParams": {}}

        for key, value in kwargs.items():
            _key: str = self.camel_to_snake_case(key)

            try:
                extractor = getattr(self, f"extract_{_key}")
            except AttributeError:
                errors["queryParams"][
                    key
                ] = f"You forgot to define `extract_{_key}` method in your class `{self.__class__.__name__}`"
                raise ValidationError(errors)

            try:
                _extracted_value = extractor(value)
            except ValidationError as error:
                errors["queryParams"][key] = str(error)
            else:
                setattr(self, _key, _extracted_value)

        if errors["queryParams"]:
            raise ValidationError(errors)


class FoodFilters(BaseFitlers):
    def extract_delivery_provider(
        self, provider: str | None = None
    ) -> DeliveryProvider | None:
        if provider is None:
            return None
        else:
            provider_name = provider.upper()
            try:
                _provider = DeliveryProvider[provider_name]
            except KeyError:
                raise ValidationError(f"Provider {provider} is not supported")
            else:
                return _provider


class FoodAPIViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        match self.action:
            case "all_orders":
                return [permissions.IsAuthenticated(), IsAdmin()]
            case _:
                return [permissions.IsAuthenticated()]

    @method_decorator(cache_page(100))
    @action(methods=["get"], detail=False)
    def dishes(self, request: Request) -> Response:
        restaurants = Restaurant.objects.all()
        serializer = RestaurantSerializer(restaurants, many=True)
        # import time
        # time.sleep(3)
        return Response(data=serializer.data)

    # HTTP POST /food/orders/
    # @transaction.atomic   <-- also available
    @action(methods=["post"], detail=False, url_path=r"orders")
    def create_order(self, request: Request) -> Response:
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assert type(request.user) is User

        with transaction.atomic():
            order = Order.objects.create(
                status=OrderStatus.NOT_STARTED,
                user=request.user,
                delivery_provider="uklon",
                eta=serializer.validated_data["eta"],
                total=serializer.calculated_total,
            )

            items = serializer.validated_data["items"]
            for dish_order in items:
                raise ValueError("some error occured")
                instance = OrderItem.objects.create(
                    dish=dish_order["dish"],
                    quantity=dish_order["quantity"],
                    order=order,
                )
                print(f"New Dish Order Item is created: {instance.pk}")

        print(f"New Food Order is created: {order.pk}. ETA: {order.eta}")

        # TODO: Run scheduler

        return Response(OrderSerializer(order).data, status=201)

    # HTTP GET /food/orders/4
    @action(methods=["get"], detail=False, url_path=r"orders/(?P<id>\d+)")
    def retrieve_order(self, request: Request, id: int) -> Response:
        order = Order.objects.get(id=id)
        serializer = OrderSerializer(order)
        return Response(data=serializer.data)

    @action(methods=["get"], detail=False, url_path=r"orders")
    def all_orders(self, request: Request) -> Response:
        # filters = FoodFilters(**request.query_params.dict())
        # status: str | None = request.query_params.get("status")
        # orders = (
        #     Order.objects.all()
        #     if filters.delivery_provider is None
        #     else Order.objects.filter(delivery_provider=filters.delivery_provider)
        # )

        orders = Order.objects.all()

        paginator = LimitOffsetPagination()
        # paginator.page_size = 2
        # paginator.page_size_query_param = "size"
        page = paginator.paginate_queryset(orders, request, view=self)

        if page is not None:
            serializer = OrderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


def import_dishes(request):
    if request.method != "POST":
        raise ValueError(f"Method {request.method} is not allowed on this resource")

    csv_file = request.FILES.get("file")
    if csv_file is None:
        raise ValueError("No CSV File Provided")

    decoded = csv_file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    total = 0

    for row in reader:
        restaurant_name = row["restaurant"]
        try:
            rest = Restaurant.objects.get(name__icontains=restaurant_name.lower())
        except Restaurant.DoesNotExist:
            print(f"Skipping restaurant {restaurant_name}")
        else:
            print(f"Restaurant {rest} found")

        Dish.objects.create(name=row["name"], price=int(row["price"]), restaurant=rest)
        total += 1

    print(f"{total} dishes uploaded to the database")

    return redirect(request.META.get("HTTP_REFERER", "/"))


router = routers.DefaultRouter()
router.register(prefix="", viewset=FoodAPIViewSet, basename="food")