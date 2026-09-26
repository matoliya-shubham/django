import time
import contextvars
import uuid
from django.http import JsonResponse

request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        id = str(uuid.uuid4())
        request_id_var.set(id)
        response = self.get_response(request)
        response["X-Request-ID"] = id
        return response
class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        print(f'method: {request.method} path: {request.path} status: {response.status_code} duration: {duration*1000:.2f}ms')
        return response

class TagMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f'TAG: before, id={request_id_var.get()}')
        response = self.get_response(request)
        print(f'TAG: after, id={request_id_var.get()}')
        return response

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = 5
        self.rate = {}

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        now = time.time()
        if ip in self.rate:
            duration = now - self.rate[ip]["window_start"]
            if duration <= 60 and self.rate[ip]["count"] >= self.limit:
                return JsonResponse({"error": "too many requests"}, status=429)
            elif duration <= 60:
                self.rate[ip]["count"] += 1
            else:
                self.rate[ip] = {"window_start": now, "count": 1}
        else:
            self.rate[ip] = {"window_start": now, "count": 1}
        response = self.get_response(request)
        print(f'rate: {self.rate}')
        return response