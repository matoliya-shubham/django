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

---

## Drill 1 — scored 3/5 (retest due)

Answered cold, no notes. Recording the **gaps**, not the wins — Q3 and Q4 were
fine and need nothing.

### Q1. Trace `/api/tasks/5/` from `wsgi.py` to the view ❌

> *I said:* "wsgi.py gets request, middleware, urls.py resolves, view runs."

Right order, but it's a **one-way trip**. A lifecycle question is always about
the round trip, and the follow-ups live in the second half.

Missing:
- `wsgi.py` doesn't "get" the request. It exposes one callable
  (`application = get_wsgi_application()`) that gunicorn imports and calls. The
  **server** owns the socket; `wsgi.py` is just the agreed handoff point.
- Django finds urls via `settings.ROOT_URLCONF` → `config.urls`, not by magic.
- **The way back out:** the `HttpResponse` travels back up through every
  middleware **in reverse order**. Proved this myself in Phase 6 with
  `TagMiddleware`: `TAG: before` → log line → `TAG: after`.
- URL resolution happens *between* the two middleware passes — middleware wraps
  resolution-**and**-view, not just the view.

**Full-marks version:**

> gunicorn receives the request → calls the WSGI callable in `wsgi.py` → Django
> builds an `HttpRequest` → middleware runs top-down → `ROOT_URLCONF` resolves
> the path, converters cast `5` to an int → view runs, returns `HttpResponse` →
> middleware runs bottom-up → server writes the bytes.

### Q2. Project vs app ❌ (mechanically right, conceptually thin)

> *I said:* "app is a folder with apps.py registered in INSTALLED_APPS."

That names the *registration*, not the *distinction*.

- `apps.py` is **not** what makes it an app. An app is any **Python package
  listed in `INSTALLED_APPS`**. `startapp` generates `apps.py` (an `AppConfig`)
  as modern convention, but the `INSTALLED_APPS` entry is what counts. Models in
  an unregistered folder are invisible — `makemigrations` won't see them.

| | project | app |
|---|---|---|
| how many | exactly one | many |
| holds | `settings.py`, `ROOT_URLCONF`, `wsgi.py`/`asgi.py` | models, views, migrations, templates |
| job | configuration + deployment unit | one feature, self-contained |
| portable? | no | **yes — should drop into another project** |

That last row is what's being fished for. `django.contrib.admin` and
`rest_framework` are just apps someone else wrote — same shape as `tasks/`.

**Direction of dependency:** `config/` imports `tasks`. `tasks` must never
import `config`. That's precisely why `tasks/urls.py` says `path("health/")` and
not `path("api/health/")` — the app doesn't know where it's mounted. My 1a bug
was this boundary being crossed.

**Portability test:** could I copy `tasks/` into another project unchanged? If
yes, it's a proper app.

### Q5. WSGI vs ASGI ❌ (the classic misconception)

> *I said:* "wsgi is sync one request at a time, asgi is async."

"One request at a time" is per **worker**, not per server. WSGI deployments
serve plenty of concurrency — gunicorn runs N worker processes (± threads), each
handling one request start to finish. **Concurrency comes from the process
model, not the protocol.** Say it flatly and you get asked how any Django site
has ever worked.

The real distinction is not speed, it's **what the protocol can express**:

| | WSGI | ASGI |
|---|---|---|
| shape | one request → one response | request/response **plus** long-lived connections |
| worker blocked during I/O | yes | no — it interleaves |
| WebSockets, SSE, HTTP/2 push | **impossible** | yes |
| servers | gunicorn, uWSGI | uvicorn, daphne, hypercorn |

WSGI has no way to *say* "this connection stays open, messages flow both ways."
Not slow at it — structurally incapable. Hence Django Channels, hence `asgi.py`.

**One-liners to have ready:**
> **WSGI** — the synchronous Python↔webserver contract: one request in, one
> response out, worker blocked throughout.
> **ASGI** — the async successor: a worker interleaves many in-flight requests
> while awaiting I/O, and can carry long-lived protocols WSGI can't represent.

**Trap for later:** ASGI only helps if the code is *actually* async. One
blocking DB call inside an `async def` view stalls the whole event loop — worse
than WSGI. See Python Interlude IV.

### Q3 ✅ `include()` — had it

Keeps each app's URLs in the app. Worth adding: the mount point lives in **one
line**, so `path("api/v2/", include("tasks.urls"))` moves every URL at once
(cheap API versioning); and `app_name` namespaces names so two apps can both
have `detail` → `reverse("tasks:detail")`. Clincher: third-party apps ship their
own `urls.py` — `include()` is the only way to mount DRF or the admin.

### Q4 ✅ trailing slash / `APPEND_SLASH` — had it

Worth adding: it lives in **`CommonMiddleware`** (default `True`), redirects
only when the slash-less URL *doesn't* match and the slashed one *does*, and
it's a **301**.

**The gotcha:** browsers turn a redirected POST into a GET and **drop the body**.
So POSTing to `/api/tasks/5` silently becomes a GET of `/api/tasks/5/` — 200 OK,
payload gone, nothing errored. Django refuses to be quiet about it under
`DEBUG=True`:

> "You called this URL via POST, but the URL doesn't end in a slash and you have
> `APPEND_SLASH` set. Django can't redirect to the slash URL while maintaining
> POST data."

`APPEND_SLASH = False` → plain 404. Stricter, arguably more honest for an API.

---

## Side questions that came up

**Running two API versions at once.** Mount the same app twice:

```python
path("api/v1/", include("tasks.urls_v1", namespace="v1")),
path("api/v2/", include("tasks.urls_v2", namespace="v2")),
```

Separate `urls_*`/`views_*` modules, **shared `models.py`** — one schema, one
migration history. The rule: **version the representation, not the data.** Only
the view/serializer layer forks; v2 usually imports v1's logic and changes the
output shape.

Two warnings: have a **deprecation plan before creating v2** (teams that don't
maintain five versions forever), and once on DRF, `URLPathVersioning` gives
`request.version` inside a *single* view — better for small differences, while
separate modules suit a real redesign.
