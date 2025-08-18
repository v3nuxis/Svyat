from dataclasses import asdict, dataclass, field
from threading import Thread
from time import sleep

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
    """Using random provider - start processing delivery orders."""

    print(f"🚚 DELIVERY PROCESSING STARTED")

    provider = uklon.Provider()
    cache = CacheService()
    order = Order.objects.get(id=order_id)

    # update order state
    order.status = OrderStatus.DELIVERY_LOOKUP
    order.save()

    # prepare data for the first request
    addresses: list[str] = []
    comments: list[str] = []
    for rest_name, address in order.delivery_meta():
        addresses.append(rest_name)
        comments.append(f"Delivery to the {address}")

    # NOTE: Only UKLON is currently supported so no selection in here
    #       just update the state here since we know the provider
    order.status = OrderStatus.DELIVERY
    order.save()

    _response: uklon.OrderResponse = provider.create_order(
        uklon.OrderRequestBody(addresses=addresses, comments=comments)
    )

    # update the cache
    tracking_order = TrackingOrder(**cache.get("orders", str(order_id)))
    tracking_order.delivery["location"] = _response.location

    # initial status
    current_status: uklon.OrderStatus = _response.status

    while current_status != uklon.OrderStatus.DELIVERED:
        response: uklon.OrderResponse = provider.get_order(_response.id)

        print(f"🚙 UKLON [{response.status}]: 📍 {response.location}")
        if current_status == response.status:
            sleep(1)
            continue

        current_status = response.status  # DELIVERY, DELIVERED
        tracking_order.delivery["location"] = response.location

        # update cache
        cache.set("orders", str(order_id), asdict(tracking_order))

    print(f"🏁 UKLON [{response.status}]: 📍 {response.location}")

    # update storage
    Order.objects.filter(id=order_id).update(status=OrderStatus.DELIVERED)

    # update the cache
    tracking_order.delivery["status"] = OrderStatus.DELIVERED
    cache.set("orders", str(order_id), asdict(tracking_order))


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
                order_in_silpo.delay(order_id=order.pk, items=items)
            case "kfc":
                order_in_kfc.delay(order_id=order.pk, items=items)
            case _:
                raise ValueError(
                    f"Restaurant {restaurant.name} is not available for processing"
                )