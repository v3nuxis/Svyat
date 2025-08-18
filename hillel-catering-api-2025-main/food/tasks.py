from celery import shared_task

@shared_task
def order_in_kfc(order_data):
    print(f"Отправляем заказ в KFC: {order_data}")

@shared_task
def order_in_silpo(order_data):
    print(f"Отправляем заказ в Сильпо: {order_data}")