import time
from dataclasses import asdict
from shared.cache import CacheService
from food.services import TrackingOrder
from food.tasks import send_uber_location

class UberClient:
    def __init__(self, order_id: int):
        self.order_id = order_id

    def start_delivery(self):
        lat, lng = 46.4825, 30.7233
        for _ in range(100):
            send_uber_location.delay(self.order_id, lat, lng)
            lat += 0.0001
            lng += 0.0001

    def stop_delivery(self):
        print(f"Delivery stopped for order {self.order_id}")