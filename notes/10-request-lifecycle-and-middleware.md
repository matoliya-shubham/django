# Chapter 10 — Request Lifecycle & Middleware

## The path

```
WSGI server → middleware chain (in) → urls.py resolves the path
→ view runs → middleware chain (out) → WSGI server
```

Middleware wraps around URL-resolution-and-view, not just the view. `urls.py`
runs *between* the two middleware passes, not before them.

## Middleware is an onion, not a list

`MIDDLEWARE` in `settings.py` looks like a flat list, but Django nests each
entry around the next at startup — first entry = outermost layer.

```python
class SomeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response   # runs ONCE, at boot — wiring

    def __call__(self, request):
        # code here runs on the way IN
        response = self.get_response(request)   # calls the next layer
        # code here runs on the way OUT
        return response
```

`get_response` is literally "the rest of the onion." `__init__` builds the
chain once; `__call__` walks one step of it, every request.

**Proved it, not just read it:** put two dummy middlewares in the list,
`TagMiddleware` before `RequestLogMiddleware`. Output was:

```
TAG: before
<RequestLogMiddleware's line>
TAG: after
```

First in the list = first to see the request, last to see the response.

**JS comparison:** same shape as Express's `(req, res, next) => {...}`. Key
difference — Django's `get_response(request)` *returns* the response, so your
"after" code has the real response object to read/modify. Express's `next()`
gives you nothing back.

## Short-circuiting

A middleware doesn't have to call `get_response` at all. If it returns its own
response instead, nothing further down the chain — no later middleware, no
view — ever runs.

```python
def __call__(self, request):
    if too_many_requests(request):
        return JsonResponse({"error": "..."}, status=429)   # chain stops here
    return self.get_response(request)
```

Built a fixed-window rate limiter this way: check *before* calling
`get_response`, not after — checking after means the view already ran even on
a request you meant to block, which defeats the entire point.

**Gotcha:** a fixed window has a real flaw — a burst at the boundary between
two windows can let through close to 2x the limit. Fine for a toy version;
know the name (fixed vs sliding window) if asked.

## `contextvars` — passing data without passing parameters

Problem: want one value (a request id) readable from any middleware or deep
inside a view, without threading it through every function signature.

```python
import contextvars
request_id_var = contextvars.ContextVar("request_id", default=None)

request_id_var.set("abc-123")   # set once, e.g. in the outermost middleware
request_id_var.get()            # readable anywhere else, no parameter passed
```

**JS comparison:** this is Python's answer to Node's `AsyncLocalStorage` /
Java's thread-locals. "Ambient" state scoped to the current request.

Proved it by reading the same `request_id_var` inside a *different*
middleware than the one that set it — same id came back, zero params passed.

A plain module-level `dict` (no `contextvars` needed) works fine for state
that isn't about "reach it from deep in the call stack" — e.g. the rate
limiter's per-IP counters, which are only ever read inside that one
middleware.

## FBV vs CBV, briefly

`urls.py` needs something callable as `view(request)`. A class isn't callable
that way directly — `SomeView.as_view()` is a classmethod that *returns* a
plain function Django can call. That returned function makes an instance
per-request and dispatches by `request.method`: `GET` → `self.get(request)`,
`POST` → `self.post(request)`.

Same "wire once (`as_view()`, at import time) vs run per-request (the
returned closure)" split as `__init__` vs `__call__` above.

Reach for a CBV when one URL needs several HTTP methods (no `if
request.method ==` ladder), or to reuse behavior via generic views
(`ListView`, `DetailView`) and mixins — not covered yet, that's later.

## Sessions

Default: database-backed. Browser cookie holds only a session **id**; the
actual data lives in a `django_session` table row looked up by that id. This
is why `SessionMiddleware` sits early in `MIDDLEWARE` — auth and anything
after it needs that row loaded first.

## Gotchas

- checking a rate/auth condition *after* calling `get_response` doesn't
  short-circuit anything — the view already ran
- resetting a counter on window-expiry but forgetting to reset the window's
  start time means the window never actually rolls over again
- `__call__` takes `request`, not `response` — `response` is a local variable
  you get back from calling `self.get_response(request)`
