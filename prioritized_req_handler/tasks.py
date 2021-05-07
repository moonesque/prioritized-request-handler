import time
import os
from celery import Celery


# Get Celery instance and configure
celery = Celery('main_celery')
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")
celery.conf.broker_transport_options = {
    'priority_steps': list(range(6)),
    'queue_order_strategy': 'priority',
}
celery.conf.worker_prefetch_multiplier = 1
celery.conf.task_acks_late = True

@celery.task(name='limited_f')
def limited_f(x, user_id):
    resp = {'init_timestamp': time.time(), 'input_x': x, 'user_id': user_id}
    time.sleep(60)
    resp['done_timestamp'] = time.time()
    return resp
