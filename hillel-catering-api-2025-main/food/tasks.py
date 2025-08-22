from celery import shared_task
import requests
from shared.cache import CacheService
from food.services import TrackingOrder, all_orders_cooked
from dataclasses import asdict
import time
from food.providers import kfc, silpo

WEBHOOK_URL = "http://localhost:8000/api/uber/webhook/"

@shared_task
def send_uber_location(order_id: int, lat: float, lng: float):
    requests.post(WEBHOOK_URL, json={"order_id": order_id, "lat": lat, "lng": lng})
    cache = CacheService()
    tracking_order = TrackingOrder(**cache.get("orders", str(order_id)))
    tracking_order.delivery.setdefault("history", [])
    tracking_order.delivery["location"] = {"lat": lat, "lng": lng}
    tracking_order.delivery["history"].append({"lat": lat, "lng": lng, "timestamp": time.time()})
    cache.set("orders", str(order_id), asdict(tracking_order))
    
@shared_task
def order_in_kfc(order_id: int):
    cache = CacheService()
    tracking_order = TrackingOrder(**cache.get("orders", str(order_id)))
    client = kfc.Client()
    restaurant = client.get_restaurant()
    
    response = client.create_order(tracking_order.restaurants[str(restaurant.pk)]["items"])
    tracking_order.restaurants[str(restaurant.pk)]["external_id"] = response.id
    tracking_order.restaurants[str(restaurant.pk)]["status"] = "COOKING"
    cache.set("orders", str(order_id), asdict(tracking_order))

@shared_task
def order_in_silpo(order_id: int):
    cache = CacheService()
    tracking_order = TrackingOrder(**cache.get("orders", str(order_id)))
    client = silpo.Client()
    restaurant = client.get_restaurant()
    
    response = client.create_order(tracking_order.restaurants[str(restaurant.pk)]["items"])
    tracking_order.restaurants[str(restaurant.pk)]["external_id"] = response.id
    tracking_order.restaurants[str(restaurant.pk)]["status"] = "COOKING"
    cache.set("orders", str(order_id), asdict(tracking_order))