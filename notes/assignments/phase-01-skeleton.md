# Phase 1 Assignments — Skeleton, Views, URLs

> Log of what the task was, what I got wrong, and why. Mistakes are the point
> of this file — the concepts I already got right live in ch2/ch4.

---

## Assignment 1a — health endpoint that actually checks the DB

**Task:** `GET /api/health/` → `{"status": "ok", "db": "up"}`, where `db` is
proved by hitting the database. Named URL. 503 when the DB is down.

**Shipped:** `tasks/views.py::health`, `tasks/urls.py` name `health`.

### What I got stuck on

**1. "I can't access `connection`"** — the editor greyed it out. The editor was
wrong. `connection` is defined at `django/db/__init__.py:43`. Checked it with
`grep -n "connection" venv/lib/python*/site-packages/django/db/__init__.py`.

> **Lesson:** when the editor and the source disagree, the source wins. Pylance
> resolving `django.http` but not a *name* inside `django.db` means the module
> is fine and only the inference failed.

**2. `connection` vs `connections`** — Django's own comment on line 42 says
*"For backwards compatibility. Prefer `connections['default']` instead."*
`connections` (plural) is the real handler, keyed by DB alias. `connection` is
just `connections["default"]` behind a proxy. Matters the day there's a read
replica: `connections["replica"]`. That's also the interview answer to *"how do
you query a secondary database?"*

**3. What SQL proves liveness?** `SELECT 1` — valid in every dialect, touches no
table of mine, forces a real round-trip.

`cursor.fetchone()` is not optional: without reading the result you've only
proved you *sent* bytes, not that the server answered.

**4. Which exception?** `django.db.DatabaseError` — the base class that
`OperationalError`, `InterfaceError` etc. inherit from. Narrow enough to be
honest, wide enough to catch a dead socket. `except Exception` is the lazy
answer an interviewer pushes on.

**5. Which status code?** 503, not 200. A health check returning 200 while the
DB is down is theatre — the load balancer keeps routing traffic to a broken pod.

```python
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    cursor.fetchone()
```

(`with` = context manager = the `finally: cursor.close()` I'd otherwise write
by hand. Python Interlude II material, met early.)

### Mistakes I actually made

| Mistake | What happened | Why |
|---|---|---|
| `path("api/health/", ...)` in `tasks/urls.py` | URL became `/api/api/health/` | `config/urls.py` already mounts the app under `api/` via `include()`. The app's own `urls.py` must be written **relative** to that prefix. |
| `views.check_health` in urls, `health` in views | `AttributeError` **at server start**, not on request | Django imports the whole URLconf at boot and resolves every view reference eagerly. A urls.py typo is a boot failure. Deliberate: fail loudly at deploy, not at 3am. |

### `reverse()` — the bit I didn't get at first

`urls.py` is a two-column phone book, and Django reads it **both ways**:

| direction | who uses it | example |
|---|---|---|
| URL → view | the browser, routing | `/api/health/` → `health()` |
| name → URL | my code, `reverse()` | `reverse("health")` → `/api/health/` |

"Reverse" = the reverse lookup. The payoff: the string `/api/health/` exists in
**exactly one place**, `urls.py`. Change the path and every `reverse("health")`,
`{% url 'health' %}` and `redirect("health")` follows automatically. Hardcoded
URL strings scattered over 40 files are the thing this deletes.

**JS comparison:** same idea as naming an Express route and generating links
from the name — except Django builds it in, and templates use it too.

---

## Assignment 1b — task detail by hand, no DRF

**Task:** `GET /api/tasks/<int:task_id>/`. 200 + task JSON, **JSON** 404 (not
Django's HTML page) when missing, 405 on any other method.

**Shipped:** `tasks/views.py::get_task`, URL name `task_detail`.

### `Http404` vs `DoesNotExist` — two different layers

```
Task.objects.get(pk=1)
      ↓ nothing found
Task.DoesNotExist          ← DATABASE language. Knows nothing about HTTP.
      ↓ I translate
JsonResponse(..., status=404)   ← HTTP language
```

- `Task.DoesNotExist` — auto-generated on every model. Raised by `.get()`.
  Would raise identically in a script with no web server running.
- `Http404` — an HTTP signal. Django's middleware catches it and renders an
  **HTML** error page.
- `get_object_or_404` — just that translation pre-packaged
  (`try/except DoesNotExist: raise Http404`).

**Why I must not use `get_object_or_404` here:** it ends in an HTML page, and an
API client asked for JSON. So I do the translation by hand.

### Mistakes I actually made

**1. Bare dict keys — the biggest JS→Python trap**

```python
{id: task.id, title: task.title}     # WRONG
{"id": task.id, "title": task.title} # right
```

JavaScript quietly quotes bare keys for you. **Python does not** — a bare name
is a variable lookup. `title` → `NameError`, loud and obvious.

But `id` **didn't** error, because `id` is a real name in Python: the builtin
function. So the dict got keyed by a *function object*, stayed legal, and only
blew up one layer later inside `json.dumps`:

> `TypeError: keys must be str, int, float, bool or None, not builtin_function_or_method`

> **Lesson:** `title` failed loudly, `id` failed quietly and the error surfaced
> two layers from where I made it. Same trap: `list`, `type`, `str`, `sum`,
> `filter`, `max`, `input`. Shadowing a builtin is legal and breaks elsewhere.

**2. Passing the model instance straight to `JsonResponse`**

```python
JsonResponse({"task": task})   # TypeError: Object of type Task is not JSON serializable
```

`json` knows dict / list / str / number / bool / None, and nothing else. A
`Task` is a Python object with a DB row behind it. I have to choose the fields
and build a plain dict myself.

> That hand-written dict, once per model per endpoint, forever — **is exactly
> what a DRF serializer replaces.** This is the gap Phase 7 fills.

**3. No 405 branch → 500**

`if request.method == "GET":` with no `else`. On POST, Python ran off the end
and returned `None`:

> `The view didn't return an HttpResponse object. It returned None instead.`

From the client's side that turns *"you used the wrong verb"* into *"the server
is broken"* — and under `DEBUG=True` it leaks a full stack trace.

**4. POST returned a 403 HTML page, not my 405**

CSRF. `CsrfViewMiddleware` rejects unsafe methods without a valid token in
`process_view`, which runs **before the view is ever called**. My 405 never got
a turn. Phase 6 paying off: middleware ordering decides who answers first.

**5. Put `csrf_exempt` in the `MIDDLEWARE` list**

Wrong mechanism. The import path says it: `django.views.**decorators**.csrf`.

| | scope |
|---|---|
| middleware | wraps **every** request in the project |
| decorator | wraps **one** view |

Exempting the whole site was never the goal.

```python
@csrf_exempt
def get_task(request, task_id):
```

**How it actually works** (neat, and it recurs): `csrf_exempt` disables nothing.
It sets an attribute — `view.csrf_exempt = True` — and `CsrfViewMiddleware`
checks for that attribute before deciding to reject. *The decorator leaves a
flag; the middleware reads it.*

**When is exempting OK?** CSRF protects **cookie-authenticated browser**
requests. An API authenticating by token header isn't vulnerable the same way —
which is why DRF turns CSRF off for token auth and keeps it on for session auth.

### Things I asked about

**Dates.** I wrote no date handling, yet a `datetime` serialized fine.
`JsonResponse` defaults to `DjangoJSONEncoder` (not the stdlib encoder), which
knows `datetime`, `date`, `Decimal`, `UUID` → emits **ISO 8601**.

```
"created_at": "2026-10-06T11:23:41.902Z"
```

- Inside `JsonResponse` — nothing to do.
- Plain `json.dumps` (Celery task, cache write) — it **will** raise. Pass
  `cls=DjangoJSONEncoder`, or `.isoformat()` the field yourself.
- Want `"06 Oct 2026"`? Don't, in an API. It can't be sorted, can't be parsed
  reliably, and bakes one locale into the backend. Send ISO; let the frontend
  format for the human.
- `USE_TZ = True` → aware **UTC** datetimes (note the `Z`). `False` → naive
  local times and timezone bugs that only appear for users in other countries.

**Response shape — envelope or flat?** A real design question, and asked.

```json
{"id": 5, "title": "Buy milk"}                    // flat — the resource IS the body
{"status": "success", "task": {"id": 5, ...}}     // enveloped
```

The HTTP status code already carries success/failure; repeating it in the body
gives two sources of truth that can disagree. Also `"status"` ended up meaning
two things at once — the envelope's success flag, and the task's `todo`/`done`.
That collision is the smell. Convention (and DRF's default): **flat for 200, a
small envelope for errors**, since an error has no natural resource to be.

**405 needs an `Allow` header** — required by the HTTP spec, not politeness. The
resource exists; only the verb is wrong, so the client is told what *is* allowed.

```python
response = JsonResponse({...}, status=405)
response["Allow"] = "GET"
```

(Same dict-style header access as the Phase 6 middleware.)

### Order of checks in the view

Method **first**, then the lookup. A POST to a non-existent task should answer
405 ("we don't do POST here"), not 404 — the verb is wrong regardless of whether
the row exists.

---

## Verifying, every time

```bash
curl -i http://127.0.0.1:8000/api/health/          # 200 / 503
curl -i http://127.0.0.1:8000/api/tasks/5/         # 200
curl -i http://127.0.0.1:8000/api/tasks/999/       # 404, JSON body
curl -i -X POST http://127.0.0.1:8000/api/tasks/5/ # 405 + Allow: GET
docker compose stop db                             # then re-curl health → 503
docker compose start db
```

`-i` matters: the status line and headers are half the assignment.

---

## Still open for Phase 1

- [ ] `wsgi.py` vs `asgi.py` — what actually serves the request
- [ ] **Drill 1** (from memory, no notes)
