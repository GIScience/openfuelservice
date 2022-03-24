from celery import Celery

from app.core.config import settings

test = settings.CELERY_BROKER_URL

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL)

celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}
