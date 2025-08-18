import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault("DJANGO_SETTINGS_MODULE",  "config.settings")

app = Celery("hillel_catering")
app.config_from_object("django_conf:settigns", namespace = "CELERY")
# app.conf.update(task_serializer="pickle")   

app.conf.task_queues = [
    Queue(
            "high_priority",
            Exchange("high_priority"),
            routing_key="high_priority",
            queue_arguments = {'x=max priority': 10},
        ),
    Queue(
        'default',
        Exchange('default'),
        routing_key='default',
    )
]

app.conf.task_default_queue = 'default'
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5

app.conf.task_routes = {
    'orders.tasks.order_in_silpo': {'queue': 'high_priority', 'priority': 10},
    'orders.tasks.order_in_kfc': {'queue': 'high_priority', 'priority': 10},
}


app.autodiscover_tasks()