import enum
from dataclasses import dataclass, asdict

import httpx

class SilpoOrder:
    def create_order(self, order_data):
        from food.tasks import order_in_silpo
        order_in_silpo.apply_async(args=(order_data,), priority=10)

class OrderStatus(enum.StrEnum):
    NOT_STARTED = "not started"
    COOKING = "cooking"
    COOKED = "cooked"
    FINISHED = "finished"


@dataclass
class OrderItem:
    dish: str
    quantity: str


@dataclass
class OrderRequestBody:
    order: list[OrderItem]


@dataclass
class OrderResponse:
    id: str
    status: OrderStatus


class Client:
    # the url of running service
    BASE_URL = "http://localhost:8001/api/orders"

    @classmethod
    def create_order(cls, order: OrderRequestBody):
        response: httpx.Response = httpx.post(cls.BASE_URL, json=asdict(order))
        response.raise_for_status()
        return OrderResponse(**response.json())

    @classmethod
    def get_order(cls, order_id: str):
        response: httpx.Response = httpx.get(f"{cls.BASE_URL}/{order_id}")
        response.raise_for_status()
        return OrderResponse(**response.json())