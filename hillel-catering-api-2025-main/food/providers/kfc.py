import random
import time
import uuid
from typing import Literal
from food.tasks import order_in_kfc
import httpx
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

OrderStatus = Literal["not started", "cooking", "cooked", "finished"]
STORAGE: dict[str, OrderStatus] = {}
CATERING_API_WEBHOOK_URL = "http://localhost:8000/webhooks/kfc/"


app = FastAPI()

class KFCOrder:
    def create_order(self, order_data):
        order_in_kfc.apply_async(args = (order_data), priority = 10)

class OrderItem(BaseModel):
    dish: str
    quantity: int


class OrderRequestBody(BaseModel):
    order: list[OrderItem]


async def update_order_status(order_id: str):
    ORDER_STATUSES: tuple[OrderStatus, ...] = ("cooking", "cooked", "finished")
    for status in ORDER_STATUSES:
        time.sleep(random.randint(4, 6))
        STORAGE[order_id] = status
        print(f"KFC: [{order_id}] --> {status}")

        if status == "finished":
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        CATERING_API_WEBHOOK_URL,
                        data={"id": order_id, "status": status},
                    )
                except httpx.ConnectError as error:
                    print("API connection failed")
                else:
                    print(
                        f"KFC: Web hook sent to the {CATERING_API_WEBHOOK_URL}. Status: {status}"
                    )


@app.post("/api/orders")
async def make_order(body: OrderRequestBody, background_tasks: BackgroundTasks):
    order_id = str(uuid.uuid4())
    STORAGE[order_id] = "not started"
    background_tasks.add_task(update_order_status, order_id)

    return {"id": order_id, "status": "not started"}


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    return STORAGE.get(order_id, {"error": "Nu such order"})