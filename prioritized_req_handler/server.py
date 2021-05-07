from sanic import Sanic
from sanic.response import text, json
from celery.result import AsyncResult
from tasks import limited_f
from utils import get_queue_number, update_user_history


sanic_app = Sanic('some_webapp')

@sanic_app.post('/task')
async def limited_f_view(request):
    """
    Endpoint accepts the intensive task and returns the 
    id of the task.
    """

    user_id = request.json['user_id']
    queue_number = get_queue_number(user_id)
    update_user_history(user_id, 6000)
    task_res = limited_f.apply_async(args=[request.json['x'], user_id], priority=queue_number)

    return json({"task_id": task_res.id, "result_url": f"/result/{task_res.id}", 'user_id': user_id})


@sanic_app.get('/result/<task_id>')
async def get_limited_f_result(request, task_id):
    """
    This endpoint accepts the task_id and returns the result if ready.
    """
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return json(result)
