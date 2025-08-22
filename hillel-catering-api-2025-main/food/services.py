from dataclasses import asdict, dataclass, field
from threading import Thread
from time import sleep
from .providers.uber import UberClient

from django.db.models import QuerySet

from config import celery_app
from shared.cache import CacheService

from .enums import OrderStatus
from .mapper import RESTAURANT_EXTERNAL_TO_INTERNAL
from .models import Order, OrderItem, Restaurant
from .providers import kfc, silpo, uklon


@dataclass
class TrackingOrder:
    """
    {
        17: {
            restaurants: {
                1: {  // internal restaurant id
                    status: NOT_STARTED, // internal
                    external_id: 13,
                    request_body: {...},
                },
                2: {  // internal restaurant id
                    status: NOT_STARTED, // internal
                    external_id: edf055b8-06e8-40ed-ab35-300fef3e0a5d,
                    request_body: {...},
                },
            },
            delivery: {...}
        },
        18: ...
    }
    """

    restaurants: dict = field(default_factory=dict)
    delivery: dict = field(default_factory=dict)


def all_orders_cooked(order_id: int):
    cache = CacheService()
    tracking_order = TrackingOrder(**cache.get(namespace="orders", key=str(order_id)))
    print(f"Checking if al orders are cooked: {tracking_order.restaurants}")

    results = all(
        (
            payload["status"] == OrderStatus.COOKED
            for _, payload in tracking_order.restaurants.items()
        )
    )

    return results


@celery_app.task(queue="high_priority")
def order_in_silpo(order_id: int, items: QuerySet[OrderItem]):
    """Short polling requests to the Silpo API

    NOTES
    get order from cache
    is external_id?
      no: make order
      yes: get order
    """

    client = silpo.Client()
    cache = CacheService()
    restaurant = Restaurant.objects.get(name="Silpo")

    def get_internal_status(status: silpo.OrderStatus) -> OrderStatus:
        return RESTAURANT_EXTERNAL_TO_INTERNAL["silpo"][status]

    cooked = False
    while not cooked:
        sleep(1)  # just a delay

        # GET ITEM FROM THE CACHE
        tracking_order = TrackingOrder(
            **cache.get(namespace="orders", key=str(order_id))
        )
        # validate
        silpo_order = tracking_order.restaurants.get(str(restaurant.pk))
        if not silpo_order:
            raise ValueError("No Silpo in orders processing")

        # PRINT CURRENT STATUS
        print(f"CURRENT SILPO ORDER STATUS: {silpo_order['status']}")

        if not silpo_order["external_id"]:
            # ✨ MAKE THE FIRST REQUEST IF NOT STARTED
            response: silpo.OrderResponse = client.create_order(
                silpo.OrderRequestBody(
                    order=[
                        silpo.OrderItem(dish=item.dish.name, quantity=item.quantity)
                        for item in items
                    ]
                )
            )
            internal_status: OrderStatus = get_internal_status(response.status)

            # UPDATE CACHE WITH EXTERNAL ID AND STATE
            tracking_order.restaurants[str(restaurant.pk)] |= {
                "external_id": response.id,
                "status": internal_status,
            }
            print(
                f"Created Silpo Order. External ID: {response.id}, Status: {internal_status}"
            )
            cache.set(
                namespace="orders", key=str(order_id), value=asdict(tracking_order)
            )
        else:
            # ✨ IF ALREADY HAVE EXTERNAL ID - JUST RETRIEVE THE ORDER
            response = client.get_order(silpo_order["external_id"])
            internal_status = get_internal_status(response.status)

            print(
                f"Tracking for Silpo Order with HTTP GET /api/orders. Status: {internal_status}"
            )

            if silpo_order["status"] != internal_status:  # STATUS HAS CHANGED
                tracking_order.restaurants[str(restaurant.pk)][
                    "status"
                ] = internal_status
                print(f"Silpo order status changed to {internal_status}")
                cache.set(
                    namespace="orders", key=str(order_id), value=asdict(tracking_order)
                )

                # if started cooking
                if internal_status == OrderStatus.COOKING:
                    Order.objects.filter(id=order_id).update(status=OrderStatus.COOKING)

            if internal_status == OrderStatus.COOKED:
                print("🍳 ORDER IS COOKED")
                cooked = True

                # 🚧 CHECK IF ALL ORDERS ARE COOKED
                if all_orders_cooked(order_id):
                    cache.set(
                        namespace="orders",
                        key=str(order_id),
                        value=asdict(tracking_order),
                    )

                    Order.objects.filter(id=order_id).update(status=OrderStatus.COOKED)


@celery_app.task(queue="default")
def order_in_kfc(order_id: int, items):
    client = kfc.Client()
    cache = CacheService()
    restaurant = Restaurant.objects.get(name="KFC")

    def get_internal_status(status: kfc.OrderStatus) -> OrderStatus:
        return RESTAURANT_EXTERNAL_TO_INTERNAL["kfc"][status]

    # GET ITEM FROM THE CACHE
    tracking_order = TrackingOrder(**cache.get(namespace="orders", key=str(order_id)))

    response: kfc.OrderResponse = client.create_order(
        kfc.OrderRequestBody(
            order=[
                kfc.OrderItem(dish=item.dish.name, quantity=item.quantity)
                for item in items
            ]
        )
    )
    internal_status: OrderStatus = get_internal_status(response.status)

    # UPDATE CACHE WITH EXTERNAL ID AND STATE
    tracking_order.restaurants[str(restaurant.pk)] |= {
        "external_id": response.id,
        "status": internal_status,
    }
    print(f"KFC Silpo Order. External ID: {response.id}, Status: {internal_status}")

    print(f"Created KFC Order. External ID: {response.id}, Status: {response.status}")
    cache.set(namespace="orders", key=str(order_id), value=asdict(tracking_order))

    # save another item for MAPPING to the INTERNAL ORDER
    cache.set(
        namespace="kfc_orders",
        key=response.id,  # external KFC ID
        value={
            "internal_order_id": order_id,
        },
    )

    if all_orders_cooked(order_id):
        cache.set(namespace="orders", key=str(order_id), value=asdict(tracking_order))
        Order.objects.filter(id=order_id).update(status=OrderStatus.COOKED)


@celery_app.task
def order_delivery(order_id: int):
    """Start processing delivery orders with Uber simulator."""

    print(f"🚚 DELIVERY PROCESSING STARTED")

    cache = CacheService()
    order = Order.objects.get(id=order_id)

    order.status = OrderStatus.DELIVERY_LOOKUP
    order.save()

    provider_name = "uber"

    if provider_name == "uber":
        client = UberClient(order_id)
        client.start_delivery()

        order.status = OrderStatus.DELIVERY
        order.save()

        tracking_order = TrackingOrder(**cache.get("orders", str(order_id)))
        tracking_order.delivery = {
            "provider": "uber",
            "status": OrderStatus.DELIVERY,
            "location": {"lat": 0, "lng": 0},
        }
        cache.set("orders", str(order_id), asdict(tracking_order))
        return

    raise ValueError("Unsupported provider for delivery")


def schedule_order(order: Order):
    """Prepare order and start delivery process."""

    cache = CacheService()
    tracking_order = TrackingOrder()

    items_by_restaurants = order.items_by_restaurant()
    for restaurant, items in items_by_restaurants.items():
        tracking_order.restaurants[str(restaurant.pk)] = {
            "external_id": None,
            "status": OrderStatus.NOT_STARTED,
        }

    cache.set(namespace="orders", key=str(order.pk), value=asdict(tracking_order))
    order_delivery.delay(order_id=order.pk)
