import requests
import time
import sys

WEBHOOK_URL = "http://host.docker.internal:8000/api/uber/webhook/"

def simulate_uber_delivery(order_id: int):
    print(f"[UBER] Starting delivery for order {order_id} -> {WEBHOOK_URL}")
    
    lat, lng = 46.4825, 30.7233
    for i in range(10):
        data = {
            "order_id": order_id,
            "latitude": lat + i * 0.0001,
            "longitude": lng + i * 0.0001,
            "status": "moving"
        }
        try:
            resp = requests.post(WEBHOOK_URL, json=data)
            print(f"[UBER] Sent update #{i+1}, status: {resp.status_code}")
        except Exception as e:
            print(f"[UBER] Error sending update: {e}")
        time.sleep(1)

if __name__ == "__main__":
    order_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    simulate_uber_delivery(order_id)