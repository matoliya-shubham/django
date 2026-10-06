from django.db import DatabaseError, connection
from django.http import JsonResponse
from .models import Task
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def ping(request):
    return JsonResponse({"message": "pong", "app" :"tasks"})


def health(request):
    """Liveness + dependency check. Proves the DB actually answers."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"status": "degraded", "db": "down"}, status=503)

    return JsonResponse({"status": "ok", "db": "up"})

@csrf_exempt
def get_task(request, task_id):
    if request.method == "GET":
        try:
            task = Task.objects.get(pk=task_id)
            task_response = {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "created_at": task.created_at.strftime("%d %b %Y")
            }
        except Task.DoesNotExist:
            return JsonResponse({"status": "not Found", "message": f"Task for id {task_id} not found"}, status=404)
        return JsonResponse({"status": "success", "task": task_response}, status=200)
    else:
        response = JsonResponse({"status": "method not Allowed", "message": "method not Allowed"}, status=405)
        response['Allow'] = 'GET'
        return response
    