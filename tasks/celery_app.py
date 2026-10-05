import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")




celery_app = Celery(
    "eval_app",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.pdf_tasks",
        "tasks.embedding_tasks",
        "tasks.evaluation_tasks",
        "tasks.exam_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=86400,  # 24 hours
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    broker_transport_options={"protocol": 2},
    result_backend_transport_options={"protocol": 2},

)

if __name__ == "__main__":
    celery_app.start()
