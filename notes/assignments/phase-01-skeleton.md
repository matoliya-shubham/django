# Phase 1 Assignments — Skeleton, Views, URLs

> What I was asked to build, what I got wrong, and why.
> The mistakes are the point of this file.

---

## Assignment 1a — a health check that really checks

**The task:** build `GET /api/health/`. It returns `{"status": "ok", "db": "up"}`.
The `db` part must be proved by actually asking the database something. Not
hardcoded. Return 503 if the database is down. Give the URL a name.

**Where the code is:** `tasks/views.py` → `health`. URL named `health`.

### What I got stuck on

**My editor said `connection` doesn't exist.** It was wrong. The name is really
there, at `django/db/__init__.py` line 43. I checked with:

```bash
grep -n "connection" venv/lib/python*/site-packages/django/db/__init__.py
```

> **Lesson:** when the editor and the source code disagree, the source wins.

**There are two things, `connection` and `connections`.** Django's own comment
says: *"For backwards compatibility. Prefer `connections['default']` instead."*

- `connections` (plural) is the real one. It is like a dictionary, one entry per
  database.
- `connection` (singular) is just a shortcut for `connections["default"]`.

This matters when a project has more than one database. Then you write
`connections["replica"]`. That is also the answer to the interview question
*"how do you query a second database?"*

**What SQL proves the database is alive?** `SELECT 1`.

It works on every database. It touches none of my tables. And it forces a real
trip to the server and back.

I also need `cursor.fetchone()`. Without it I have only proved that I *sent*
something. I have not proved the database *answered*.

**Which error do I catch?** `django.db.DatabaseError`.

It is the parent class of `OperationalError`, `InterfaceError` and the rest. So
it catches a dead database but does not catch every bug in my code. Writing
`except Exception` is the lazy version, and an interviewer will push on it.

**Which status code?** 503, not 200.

A health check that says 200 while the database is dead is useless. The load
balancer will keep sending real users to a broken server.

```python
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    cursor.fetchone()
```

The `with` here is a *context manager*. It closes the cursor for me, even if an
error is thrown. It is the same as writing `finally: cursor.close()` by hand.

### Mistakes I actually made

**1. I wrote `path("api/health/", ...)` inside `tasks/urls.py`.**

The URL became `/api/api/health/`.

Why: `config/urls.py` already mounts the app under `api/`. So inside the app I
must write paths *without* that prefix. The app does not know where it is
mounted.

**2. My URL pointed at `views.check_health` but the function was called `health`.**

The error came up **when I started the server**, not when I visited the URL:

```
AttributeError: module 'tasks.views' has no attribute 'check_health'
```

Why: Django reads the whole URL file at startup and checks every view exists.
So a typo in `urls.py` stops the server from booting.

That is on purpose. Better to break loudly at deploy time than at 3am when a
user finally hits that one URL.

### `reverse()` — the bit I did not get at first

Think of `urls.py` as a phone book with two columns:

| name | URL |
|---|---|
| `"health"` | `/api/health/` |
| `"ping"` | `/api/ping/` |

Django reads it in **both** directions.

**Left to right:** a browser asks for `/api/health/`, Django finds the view.
That is normal routing.

**Right to left:** my code asks "what is the URL named `health`?" and Django
answers `/api/health/`. That is `reverse()`. It is literally the reverse lookup.

```python
reverse("health")   # → "/api/health/"
```

**Why bother?** Because the text `/api/health/` now exists in exactly **one**
place: `urls.py`.

Imagine 40 files with `"/api/health/"` typed inside them. Then the URL changes.
You have to find all 40 and pray you did not miss one. With `reverse()` you
change one line and everything follows.

**Compared to JS:** the same idea as naming a route in Express and building
links from the name. Django just builds it in, and templates use it too with
`{% url 'health' %}`.

---

## Assignment 1b — fetch one task by id, by hand

**The task:** build `GET /api/tasks/<int:task_id>/` without DRF.

| request | response |
|---|---|
| `GET` on an id that exists | 200 and the task as JSON |
| `GET` on an id that does not exist | 404, **with a JSON body** |
| `POST` / `PUT` / `DELETE` | 405 |

**Where the code is:** `tasks/views.py` → `get_task`. URL named `task_detail`.

### `Http404` and `DoesNotExist` are two different things

They live at two different levels.

```
Task.objects.get(pk=1)
      ↓ found nothing
Task.DoesNotExist          ← database language. Knows nothing about the web.
      ↓ I translate it
JsonResponse(..., status=404)   ← web language
```

- **`Task.DoesNotExist`** is made automatically for every model. `.get()` raises
  it. It would raise the same way in a plain script with no web server at all.
- **`Http404`** is a web thing. Django catches it and shows an **HTML** error
  page.
- **`get_object_or_404`** is just those two steps packaged together.

**So why could I not use `get_object_or_404`?** Because it ends in an HTML page.
My API client asked for JSON. So I do the translation myself.

### Mistakes I actually made

**1. I wrote dict keys without quotes. This is the biggest JS → Python trap.**

```python
{id: task.id, title: task.title}      # WRONG
{"id": task.id, "title": task.title}  # right
```

In JavaScript, `{id: 1}` makes the key the *text* `"id"`. JS quietly adds the
quotes for you.

**Python does not.** In Python a bare word means "look up the variable with this
name". There is no variable called `title`, so I got a `NameError`. Loud and
clear.

But `id` did **not** error. Because `id` *is* a real name in Python — it is a
built-in function. So Python happily used that function as a dictionary key.
Everything looked fine until `json.dumps` tried to turn it into JSON:

```
TypeError: keys must be str, int, float, bool or None,
           not builtin_function_or_method
```

> **Lesson:** `title` failed straight away. `id` failed quietly, and the error
> appeared two steps later in a completely different place.
>
> Other built-in names that do the same: `list`, `type`, `str`, `sum`, `filter`,
> `max`, `input`. Using them as your own names is allowed, and it breaks
> something else later.

**2. I passed the model object straight to `JsonResponse`.**

```python
JsonResponse({"task": task})
# TypeError: Object of type Task is not JSON serializable
```

JSON only understands dictionaries, lists, text, numbers, true/false and null.
That is the whole list. A `Task` is a Python object with a database row behind
it. JSON has no idea how to flatten it.

So I pick which fields to send and build a plain dictionary myself.

> That hand-written dictionary — once per model, for every endpoint, forever —
> **is exactly what a DRF serializer replaces.** This is the gap Phase 7 fills.

**3. I forgot the 405 branch, and got a 500 instead.**

I wrote `if request.method == "GET":` with no `else`. On a POST, Python ran off
the end of the function and returned `None`:

```
The view didn't return an HttpResponse object. It returned None instead.
```

So "you used the wrong method" turned into "the server is broken". And with
`DEBUG=True` it also showed a full stack trace to the client.

**4. A POST gave me a 403 HTML page, not my 405.**

That is CSRF protection.

`CsrfViewMiddleware` blocks POST, PUT and DELETE that arrive without a valid
CSRF token. It does this **before my view ever runs**. So my 405 never got a
chance.

This is Phase 6 paying off: middleware order decides who answers first.

**5. I put `csrf_exempt` in the `MIDDLEWARE` list.**

Wrong place. The import path even says so: `django.views.**decorators**.csrf`.

| | what it wraps |
|---|---|
| middleware | **every** request in the whole project |
| decorator | **one** view |

Turning CSRF off for the entire site was never what I wanted.

```python
@csrf_exempt
def get_task(request, task_id):
```

**How it actually works, which is neat:** `csrf_exempt` turns nothing off by
itself. It just sets a flag on the function — `view.csrf_exempt = True`. Then
`CsrfViewMiddleware` looks for that flag before deciding to block.

*The decorator leaves a note; the middleware reads it.*

**When is turning CSRF off safe?** CSRF protects requests authenticated by
**cookies in a browser**. An API that authenticates with a token in a header is
not open to the same attack. That is why DRF switches CSRF off for token auth
and keeps it on for session auth.

### Things I asked about

**Dates.** I wrote no date code at all, yet a `datetime` turned into JSON fine.

`JsonResponse` uses `DjangoJSONEncoder` instead of the plain Python one. That
encoder knows `datetime`, `date`, `Decimal` and `UUID`. It writes them as
**ISO 8601**:

```
"created_at": "2026-10-06T11:23:41.902Z"
```

That is the right format to send. It is unambiguous, it sorts correctly as plain
text, and every language can read it (`new Date(str)` in JS,
`datetime.fromisoformat` in Python).

- Inside `JsonResponse` — nothing to do, it is handled.
- With plain `json.dumps` (in a Celery task, or writing to a cache) — it **will**
  crash. Either pass `cls=DjangoJSONEncoder`, or call `.isoformat()` yourself.
- Want `"06 Oct 2026"` instead? Do not do that in an API. It cannot be sorted,
  it is hard to parse, and it locks one country's format into the backend. Send
  ISO and let the frontend format it for the human.
- `USE_TZ = True` means Django gives you UTC times with timezone info — that is
  what the `Z` means. With `False` you get plain local times, and timezone bugs
  that only show up for users in other countries.

**What shape should the response be?** This is a real design decision, and it
gets asked.

```json
{"id": 5, "title": "Buy milk"}                    // flat — the body IS the task
{"status": "success", "task": {"id": 5, ...}}     // wrapped in an envelope
```

The HTTP status code already says whether it worked. Repeating that in the body
gives you two sources of truth that can disagree.

I also ended up with `"status"` meaning two different things at once: the
envelope's success flag, and the task's own `todo`/`done`. That clash is the
warning sign.

The common choice, and DRF's default: **flat for success, a small envelope for
errors** — because an error has no natural object to be.

**A 405 must include an `Allow` header.** This is required by the HTTP spec, not
just politeness. The resource exists; only the verb is wrong. So the client is
told which verbs *do* work.

```python
response = JsonResponse({...}, status=405)
response["Allow"] = "GET"
```

(Same `response["Header"] = value` style as the Phase 6 middleware.)

### What order to check things in

Check the **method first**, then look up the task.

A POST to a task that does not exist should answer 405, not 404. The verb is
wrong either way, so there is no point looking the row up.

---

## How to test it

```bash
curl -i http://127.0.0.1:8000/api/health/          # 200, or 503
curl -i http://127.0.0.1:8000/api/tasks/5/         # 200
curl -i http://127.0.0.1:8000/api/tasks/999/       # 404 with a JSON body
curl -i -X POST http://127.0.0.1:8000/api/tasks/5/ # 405 and Allow: GET

docker compose stop db     # then call health again → 503
docker compose start db
```

Use `-i`. The status line and the headers are half of what I am checking.

---

## Drill 1 — scored 3/5, needs a retest

Answered with no notes. Recording the **gaps** only. Q3 and Q4 were fine.

### Q1. Trace `/api/tasks/5/` from `wsgi.py` to the view ❌

> *I said:* "wsgi.py gets request, middleware, urls.py resolves, view runs."

The order is right, but it is only half the journey. The response has to get
back out again, and that is where the follow-up questions live.

What I missed:

- `wsgi.py` does not "get" the request. It just exposes one function
  (`application = get_wsgi_application()`). Gunicorn imports that function and
  calls it. The **server** owns the network connection. `wsgi.py` is only the
  agreed meeting point.
- Django finds the URLs through `settings.ROOT_URLCONF`, which points at
  `config.urls`.
- **The way back:** the response travels back up through every middleware, in
  **reverse order**. I proved this myself in Phase 6 with `TagMiddleware`:
  `TAG: before` → log line → `TAG: after`.
- URL matching happens *between* the two middleware passes. Middleware wraps the
  URL matching as well as the view.

**The full answer:**

> Gunicorn receives the request. It calls the function in `wsgi.py`. Django
> builds an `HttpRequest`. Middleware runs top to bottom. `ROOT_URLCONF` matches
> the path and turns `5` into an int. The view runs and returns an
> `HttpResponse`. Middleware runs bottom to top. The server sends the bytes.

### Q2. Project vs app ❌ (right mechanism, missing the idea)

> *I said:* "app is a folder with apps.py registered in INSTALLED_APPS."

That describes how an app is *registered*. The question was about the
*difference*.

`apps.py` is not what makes something an app. An app is any **Python package
listed in `INSTALLED_APPS`**. `startapp` creates `apps.py` because that is the
modern style, but the entry in `INSTALLED_APPS` is what counts. Models in a
folder that is not listed are invisible — `makemigrations` will not see them.

| | project | app |
|---|---|---|
| how many | exactly one | as many as you like |
| contains | `settings.py`, `ROOT_URLCONF`, `wsgi.py`, `asgi.py` | models, views, migrations, templates |
| job | configuration and deployment | one feature, self-contained |
| can it move to another project? | no | **yes — that is the point** |

That last row is what the interviewer is after. `django.contrib.admin` and
`rest_framework` are just apps that somebody else wrote. Same shape as `tasks/`.

**Which way the dependency points:** `config/` imports `tasks`. `tasks` must
never import `config`. That is exactly why `tasks/urls.py` says `path("health/")`
and not `path("api/health/")` — the app does not know where it is mounted. My 1a
bug was this rule being broken.

**The test:** could I copy `tasks/` into another project unchanged? If yes, it is
a proper app.

### Q5. WSGI vs ASGI ❌ (the classic wrong answer)

> *I said:* "wsgi is sync one request at a time, asgi is async."

"One request at a time" is true per **worker**, not per server.

A WSGI site handles plenty of requests at once. Gunicorn runs several worker
processes, and each one handles a single request from start to finish.
**The concurrency comes from running many workers, not from the protocol.**

Say "one request at a time" flatly and you will be asked how any Django site has
ever worked.

The real difference is not speed. It is **what the protocol can express**:

| | WSGI | ASGI |
|---|---|---|
| shape | one request in, one response out | that, **plus** connections that stay open |
| is the worker stuck during I/O? | yes | no — it can work on other requests |
| WebSockets, server-sent events, HTTP/2 push | **impossible** | yes |
| servers | gunicorn, uWSGI | uvicorn, daphne, hypercorn |

WSGI has no way to even *describe* "this connection stays open and messages flow
both ways". It is not slow at it — it simply cannot say it. That is why Django
Channels exists, and why `asgi.py` appeared.

**One-line answers to have ready:**

> **WSGI** — the older, synchronous agreement between Python and the web server.
> One request in, one response out, and the worker is busy the whole time.
>
> **ASGI** — the async replacement. One worker can juggle many requests while
> waiting on I/O, and it can carry long-lived connections like WebSockets.

**A trap for later:** ASGI only helps if your code is *actually* async. One
blocking database call inside an `async def` view freezes the whole event loop —
which is worse than WSGI. See Python Interlude IV.

### Q3 ✅ Why `include()` — I had this

It keeps each app's URLs inside the app.

Worth adding: the prefix lives in **one line**, so
`path("api/v2/", include("tasks.urls"))` moves every URL in the app at once —
cheap API versioning. And `app_name` adds a namespace, so two apps can both have
a URL called `detail`: `reverse("tasks:detail")`.

The clincher: apps you install from pip ship their own `urls.py`. `include()` is
the only way to mount DRF or the admin.

### Q4 ✅ Trailing slash and `APPEND_SLASH` — I had this

Worth adding: it lives in **`CommonMiddleware`** and defaults to `True`. It only
redirects when the URL without the slash does **not** match and the one with the
slash **does**. And it is a **301**.

**The trap:** browsers turn a redirected POST into a GET and **throw the body
away**. So a POST to `/api/tasks/5` quietly becomes a GET of `/api/tasks/5/`.
You get a 200. Your data is gone. Nothing errored.

Django refuses to stay quiet about this when `DEBUG=True`:

> "You called this URL via POST, but the URL doesn't end in a slash and you have
> `APPEND_SLASH` set. Django can't redirect to the slash URL while maintaining
> POST data."

Setting `APPEND_SLASH = False` gives a plain 404 instead. Stricter, and arguably
more honest for an API.

---

## Side question: running two API versions at once

Mount the same app twice, under different prefixes:

```python
path("api/v1/", include("tasks.urls_v1", namespace="v1")),
path("api/v2/", include("tasks.urls_v2", namespace="v2")),
```

Separate `urls_*` and `views_*` files, but **one shared `models.py`**. One
schema, one migration history.

**The rule: version the output, not the data.** Only the view and serializer
layer splits in two. v2 usually imports v1's logic and just changes the shape of
the response.

Two warnings:

- **Decide how v1 will die before you create v2.** Teams that skip this end up
  maintaining five versions forever.
- Once on DRF, `URLPathVersioning` gives you `request.version` inside a *single*
  view. Better when the differences are small. Separate files are better when v2
  is a genuine redesign.

---

## Still open for Phase 1

- [ ] `wsgi.py` vs `asgi.py` — what actually serves the request
- [ ] **Drill 1 retest** — Q1, Q2, Q5, from memory
