# Chapter 4 — Apps, Views and URLs (my first endpoint)

## Step 8 — Create an app

```bash
python manage.py startapp tasks
```

### Project vs App — THE core Django idea

| | What it is | How many |
|---|---|---|
| **project** (`config/`) | the whole deployable thing: settings, root URLs, one database | exactly 1 |
| **app** (`tasks/`) | a self-contained feature: its own models, views, urls, admin, tests | many |

My task manager will end up with `tasks/`, `projects/`, `accounts/` — each
owning one slice of the domain.

**JS comparison:** in Express I'd hand-roll `routes/tasks.js` +
`models/Task.js` + `controllers/tasks.js` — one feature scattered across three
folders, grouped **by layer**. Django groups **by feature**: everything about
tasks lives inside `tasks/`. Closest JS analogue is a NestJS module.

**Payoff:** apps are portable. `django.contrib.admin` and `django.contrib.auth`
are just apps somebody else wrote — that's why I get a free admin panel and a
free user system.

### What startapp generated

```
tasks/__init__.py      marks the folder as an importable Python package
tasks/views.py         my controllers (request -> response)
tasks/models.py        my database tables
tasks/admin.py         registers models into the free admin panel
tasks/apps.py          this app's own config/metadata
tasks/tests.py         tests for this app
tasks/migrations/      generated DB change scripts land here
```

- **No `urls.py` is generated.** Django expects me to write it myself.
- `admin.py` and `tests.py` exist by default — Django's opinion is that admin
  and tests are not optional extras.

### GOTCHA — startapp does NOT register the app

The folder exists but `INSTALLED_APPS` still lists only Django's 6 built-ins.
Nothing in `tasks/` fully works (models especially) until I add it by hand.
No `npm install`-style auto-wiring here.

---

## Step 9 — My first endpoint: GET /api/ping/

Four edits, they only make sense together.

### 9.1 Register the app — `config/settings.py`

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # we have to manually add our app here
    "tasks",
]
```

The trailing comma after the last list item is legal and idiomatic Python. Keep it.

### 9.2 The view — `tasks/views.py`

```python
from django.http import JsonResponse


def ping(request):
    return JsonResponse({"message": "pong", "app": "tasks"})
```

A Django **view** = a function that takes a `request` and RETURNS a response.

```js
// Express equivalent
app.get('/ping', (req, res) => {
  res.json({ message: 'pong', app: 'tasks' })
})
```

Two real differences:
1. **There is no `res` object.** I `return` the response instead of calling a
   method on a writer. This makes views trivially testable: call the function,
   inspect the returned value.
2. **The route is NOT declared here.** Express glues path + handler in one
   `app.get(...)` call. Django keeps handlers in `views.py` and paths in
   `urls.py`, on purpose.

`JsonResponse(dict)` = `res.json(obj)`. A Python `dict` (`{"a": 1}`) is the
equivalent of a JS object literal — same syntax, but keys must be quoted.

### 9.3 The app's URL table — `tasks/urls.py` (NEW FILE)

```python
from django.urls import path
from . import views          # import views from the same folder

urlpatterns = [
    path("ping/", views.ping, name="ping"),
]
```

- `from . import views` -> `.` means "this same folder" = `require('./views')`
- `urlpatterns` must be spelled exactly that — Django looks it up by name.
- `views.ping` has **NO parentheses**: I pass the function itself, not its
  result. Same as `app.get('/ping', ping)` vs the bug `app.get('/ping', ping())`.
- `name="ping"` -> a label so I can generate this URL elsewhere instead of
  hardcoding the path string. Optional, but standard practice.
- Django convention is a **trailing slash**: `"ping/"`, not `"ping"`.

### 9.4 Mount it in the project — `config/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("tasks.urls")),
]
```

`include()` hands everything under a prefix to another URL file:

```js
app.use('/api', tasksRouter)   // the Express equivalent
```

So `api/` + `ping/` = **`/api/ping/`**.

### Test it

```bash
python manage.py runserver
# open http://127.0.0.1:8000/api/ping/
```

Result:

```json
{ "message": "pong", "app": "tasks" }
```

### The request lifecycle (what actually happened)

```
browser GET /api/ping/
  -> config/urls.py     matches "api/"  -> hands the rest ("ping/") onward
  -> tasks/urls.py      matches "ping/" -> calls views.ping
  -> tasks/views.py     ping(request) returns JsonResponse
  -> Django serialises it to JSON + sets Content-Type: application/json
  -> browser
```

Express does the same thing; the difference is that Django splits the route
table into a tree of files, one table per app.

### Small style tip
End every file with a newline (POSIX convention). Editors usually do it if I
enable "insert final newline" — keeps diffs clean.
