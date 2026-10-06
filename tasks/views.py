from django.db import DatabaseError, connection
from django.http import JsonResponse


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


