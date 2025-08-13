from time import sleep
from dataclasses import dataclass, field, asdict
from django.db.models import QuerySet

from shared.cache import CacheService

from .models import Order, Restaurant, OrderItem
from .enums import OrderStatus
from .providers import silpo
from .mapper import RESTAURANT_EXTERNAL_TO_INTERNAL


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
    print(f"Checking if al lorders are cooked: {tracking_order.restaurants}")

    results = all(
        (
            payload["status"] == OrderStatus.COOKED
            for _, payload in tracking_order.restaurants.items()
        )
    )

    return results


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
            cache.set(
                namespace="orders", key=str(order_id), value=asdict(tracking_order)
            )
        else:
            # ✨ IF ALREADY HAVE EXTERNAL ID - JUST RETRIEVE THE ORDER
            response = client.get_order(order_id)
            internal_status = get_internal_status(response.status)
            print("Tracking for Silpo Order with HTTP GET /orders")

            if silpo_order["status"] != internal_status:  # STATUS HAS CHANGED
                tracking_order.restaurants[str(restaurant.pk)][
                    "status"
                ] = internal_status
                print(f"Silpo order status changed to {internal_status}")
                cache.set(
                    namespace="orders", key=str(order_id), value=asdict(tracking_order)
                )
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

                    # TODO: 💣 UPDATE DATABASE INSTANCE


def order_in_kfc(order_id: int, items):
    pass




def schedule_order(order: Order):
    # define service3s and data state
    cache = CacheService()
    tracking_order = TrackingOrder()

    items_by_restaurants = order.items_by_restaurant()
    for restaurant, items in items_by_restaurants.items():
        # update tracking order instance to be saved to the cache
        tracking_order.restaurants[str(restaurant.pk)] = {
            "external_id": None,
            "status": OrderStatus.NOT_STARTED,
        }

    # update cache insatnce only once in the end
    cache.set(namespace="orders", key=str(order.pk), value=asdict(tracking_order))

    # start processing after cache is complete
    for restaurant, items in items_by_restaurants.items():
        match restaurant.name.lower():
            case "silpo":
                order_in_silpo(order.pk, items)
            case "kfc":
                order_in_kfc(order.pk, items)
            case _:
                raise ValueError(
                    f"Restaurant {restaurant.name} is not available for processing"
                )