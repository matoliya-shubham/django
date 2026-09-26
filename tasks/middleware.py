import time

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
        print(f'TAG: before')
        response = self.get_response(request)
        print(f'TAG: after')
        return response