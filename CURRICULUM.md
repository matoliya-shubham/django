# Curriculum & Progress Tracker

> **Read this first, every session.** It is the single source of truth for what
> is done, what is next, and what homework is outstanding.
> `NOTES.md` indexes the *notes*. This file tracks the *plan*.

**Goal:** be interview-ready on Python + Django backend roles, not just able to
follow a tutorial.

Legend: `[x]` done · `[ ]` not started · `[~]` partially done

---

## How this works

- Each phase has **topics** (checkboxes) and, at the end, **assignments**.
- Every phase ships **two assignments**: one **easy** (can I do the thing) and
  one **medium-hard** (usually extending the easy one — closer to what an
  interviewer actually probes).
- Every phase ends with an **interview drill**: questions to answer out loud,
  from memory, no notes. If I can't, the phase isn't done.
- **Python interludes** are interleaved between Django phases. Django
  interviews are half Python interviews; skipping these is the classic mistake.
- Assignment code lives in `practice/`, one folder per assignment
  (`practice/a3-orm-reports/`). Django assignments go in the `tasks` app
  unless stated otherwise.

**Rule:** a phase is only `[x]` when the notes exist AND both assignments are
done AND the drill was answered from memory.

### The tracking contract

Claude starts every session cold — no memory of the last one. This repo *is*
the memory, so a claim with nothing behind it is invisible next time.

| Layer | What it is | Trust |
|---|---|---|
| checkbox here | the claim | low — cheap to tick |
| `practice/<slug>/` or app code | the proof | high — it either exists or doesn't |
| `git log` | the timeline | highest |

- **Commit after every assignment.** A ticked box with no commit behind it is
  the one failure mode this setup cannot catch. Message format:
  `Assignment 3b: prove the N+1 with query counts`.
- Claude ticks boxes **after reading the code**, not on my say-so.
- **Drills must be done live**, in a session — answered out loud in chat and
  checked. They leave no artifact, so they can't be claimed between sessions.

---

## Status at a glance

| Phase | Topic | Notes | Assignments | Drill |
|---|---|---|---|---|
| 0 | Setup: venv, pip | ✅ ch1 | n/a | ☐ |
| P-I | **Python I** — core syntax & data model | ✅ ch3 | ☐ ☐ | ☐ |
| 1 | Project skeleton, apps, views, urls | ✅ ch2,4 | ☐ ☐ | ☐ |
| 2 | Models + migrations + Postgres | ✅ ch5,6 | ☐ ☐ | ☐ |
| 3 | The ORM | ✅ ch7 | ☐ ☐ | ☐ |
| 4 | Relations | ✅ ch8 | ☐ ☐ | ☐ |
| 5 | Django Admin | ✅ ch9 | ☐ ☐ | ☐ |
| P-II | **Python II** — functions, decorators, generators | ☐ | ☐ ☐ | ☐ |
| 6 | Request lifecycle, middleware, CBVs | ☐ | ☐ ☐ | ☐ |
| 7 | DRF: serializers, viewsets, routers | ☐ | ☐ ☐ | ☐ |
| P-III | **Python III** — OOP & the object model | ☐ | ☐ ☐ | ☐ |
| 8 | Auth, custom user, permissions, JWT | ☐ | ☐ ☐ | ☐ |
| 9 | Query optimization, indexes, transactions | ☐ | ☐ ☐ | ☐ |
| 10 | Testing | ☐ | ☐ ☐ | ☐ |
| P-IV | **Python IV** — concurrency, GIL, async | ☐ | ☐ ☐ | ☐ |
| 11 | Caching, signals, Celery | ☐ | ☐ ☐ | ☐ |
| 12 | Security | ☐ | ☐ ☐ | ☐ |
| 13 | Settings, env, deployment | ☐ | ☐ ☐ | ☐ |
| 14 | Capstone: Task Manager API end to end | ☐ | ☐ | ☐ |

**Right now:** Phase 5 notes are written; its assignments and every earlier
drill are outstanding. Next new material is **Python II**, then **Phase 6**.

---

## Phase 0 — Setup ✅

- [x] virtualenv, `activate`, the two-Pythons gotcha
- [x] `pip install`, `requirements.txt`
- [x] `docker compose` for Postgres

No assignment. Interview value is low, but "how do you isolate dependencies"
does get asked — know `venv` vs `pipenv` vs `poetry` vs `uv` exist.

---

## Python Interlude I — core syntax & data model

> Notes: **not written yet** (ch3 is a partial crash course — needs finishing)

- [x] imports, `def`, indentation, `try/except`, `__name__ == "__main__"`
- [ ] list / tuple / set / dict — when each, and the cost of each operation
- [ ] mutability, and why `def f(x=[])` is a trap
- [ ] `is` vs `==`, small-int caching
- [ ] slicing, negative indices, `[::-1]`
- [ ] comprehensions (list/dict/set) and when they hurt readability
- [ ] truthiness, `None`, `or` as a default
- [ ] f-strings, `str` vs `bytes`
- [ ] shallow vs deep copy
- [ ] `collections`: `defaultdict`, `Counter`, `namedtuple`, `deque`

### Assignment P-I-a (easy) — `practice/pi-a-wordfreq/`
CLI that reads a text file and prints the 10 most common words, case-folded,
punctuation stripped. Write it twice: once with a plain `dict`, once with
`collections.Counter`.
**Interview angle:** the single most-asked Python warm-up. They watch whether
you know `Counter` and `most_common`, and whether you `.get(k, 0)` or reach
for `defaultdict`.

### Assignment P-I-b (med-hard) — extend it
Add: group words that are anagrams of each other, and report the largest
group. Then add `--top N` and `--min-length N` flags via `argparse`.
**Interview angle:** anagram grouping is a top-5 FAANG screen question. The
insight is `sorted(word)` (or a letter-count tuple) as a dict key — i.e. *what
can be a dict key and why*. Expect the follow-up: "why must a key be hashable?"

### Drill P-I
1. Why is a mutable default argument evaluated once, and what breaks?
2. `list` vs `tuple` — beyond "one is immutable", why does it matter?
3. What makes an object hashable? Why can't a `list` be a dict key?
4. `a = [1,2]; b = a[:]` — deep copy or shallow? What breaks with nested lists?
5. Time complexity of `x in list` vs `x in set`. Why?

---

## Phase 1 — Project skeleton, apps, views, urls ✅ notes

- [x] `startproject` vs `startapp`, project vs app
- [x] every generated file, read line by line
- [x] `urlpatterns`, `path()`, `include()`
- [x] first endpoint returning `JsonResponse`
- [ ] `wsgi.py` vs `asgi.py` — what actually serves the request
- [ ] named URLs and `reverse()`

### Assignment 1a (easy) — in `tasks/`
Add `GET /api/health/` returning `{"status": "ok", "db": "up"}`, where `db` is
determined by actually hitting the database, not hardcoded. Use a named URL.
**Interview angle:** "how would you add a health check?" is a standard
systems-design-lite question. The real answer: a health check that doesn't
check dependencies is theatre.

### Assignment 1b (med-hard)
Add `GET /api/tasks/<int:id>/` by hand — no DRF. Return 404 with a JSON body
(not Django's HTML 404) when the id doesn't exist, and 405 on a non-GET.
**Interview angle:** forces you to explain the difference between
`Http404`, `get_object_or_404`, and returning `JsonResponse(status=404)` — and
why DRF exists at all. You'll appreciate Phase 7 much more after doing this
manually.

### Drill 1
1. A request hits `/api/tasks/1/`. Trace it from `wsgi.py` to your view.
2. Project vs app — what actually makes a directory an app?
3. Why `include()` instead of listing every url in `config/urls.py`?
4. What does the trailing slash do, and what is `APPEND_SLASH`?
5. WSGI vs ASGI, in one sentence each.

---

## Phase 2 — Models, migrations, Postgres ✅ notes

- [x] `models.Model`, field types, `null` vs `blank`
- [x] `makemigrations`, reading the generated file, `sqlmigrate`, `migrate`
- [x] Postgres in Docker, volumes, `.env`, psycopg 3, DBeaver
- [x] the `django_migrations` table
- [ ] `Meta`: `ordering`, `db_table`, `unique_together` / `constraints`
- [ ] data migrations (`RunPython`) vs schema migrations
- [ ] how to safely reverse / squash a migration

### Assignment 2a (easy)
Add a `Tag` model (`name`, unique) and a `ManyToManyField` from `Task`. Run
`makemigrations`, then read the generated **join table** in DBeaver before
migrating. Add a `Meta.ordering` to `Task` so newest comes first.
**Interview angle:** "how does Django model a many-to-many?" — they want to
hear *hidden join table*, and that you can name it explicitly with `through`.

### Assignment 2b (med-hard)
Add a `slug` field to `Project`, non-null and unique. Existing rows have no
slug — so this must be **three migrations**: add nullable, a `RunPython` data
migration backfilling slugs from `name`, then alter to `null=False, unique=True`.
**Interview angle:** *the* classic migrations question — "how do you add a
non-null column to a table that already has data, with zero downtime?" The
three-step dance is the expected answer, and almost nobody has done it.

### Drill 2
1. `null=True` vs `blank=True` — which layer does each affect?
2. Where does a `default=` actually get applied — Python or the DB?
3. You ran `makemigrations` on a laptop and a teammate did too. Conflict. Now what?
4. What is `django_migrations` and what happens if you delete a row from it?
5. How would you roll back a migration that's already in production?

---

## Phase 3 — The ORM ✅ notes

- [x] `manage.py shell`, manager, `objects`
- [x] create / filter / get / update / delete
- [x] `__` lookups, lazy QuerySets, `Q` and `F`
- [ ] `annotate` vs `aggregate`
- [ ] `values()` / `values_list()` / `only()` / `defer()`
- [ ] `bulk_create`, `bulk_update`, `iterator()`
- [ ] when the queryset actually hits the DB (evaluation triggers)

### Assignment 3a (easy) — `practice/a3-orm-reports/`
A management command `python manage.py report` printing: task count per status,
tasks overdue today, and the 5 most recently updated. Pure ORM, no Python
loops doing the counting.
**Interview angle:** `annotate` + `Count` + `filter` ordering. Also introduces
management commands, which come up constantly in "how do you run a cron job?"

### Assignment 3b (med-hard)
Same report, but: it must run in a **fixed number of queries regardless of how
many projects exist**, and you must prove it. Wrap it with
`django.test.utils.CaptureQueriesContext` (or `connection.queries`) and print
the query count. Then seed 1,000 tasks with `bulk_create` and confirm the count
didn't change.
**Interview angle:** "how do you find and fix an N+1?" — the single most common
Django interview question. Being able to *measure* it, not just recite
`select_related`, is what separates candidates.

### Drill 3
1. When does a QuerySet actually execute? Name three triggers.
2. `filter().filter()` vs `filter(a, b)` — same result? (Careful: across a
   multi-valued relation, no.)
3. `annotate` vs `aggregate`.
4. What is `F()` for, and what race condition does it fix?
5. `get()` raises on zero and on many. Which exceptions, and how do you handle both?

---

## Phase 4 — Relations ✅ notes

- [x] `ForeignKey`, `project_id`, `related_name`
- [x] spanning lookups with `__`, `.distinct()`
- [x] N+1, `select_related` vs `prefetch_related`
- [x] `on_delete` options
- [ ] `ManyToManyField` with a `through` model
- [ ] `OneToOneField` in practice
- [ ] self-referential FK (`"self"`) — subtasks

### Assignment 4a (easy)
Give `Task` a self-referential `parent` FK so tasks can have subtasks. Print a
project's tasks as an indented tree in the shell.
**Interview angle:** self-referential FK and "how do you store a hierarchy in a
relational DB?" — leads to adjacency list vs nested set vs materialized path.

### Assignment 4b (med-hard)
Replace the plain M2M from 2a with a `through` model `TaskTag` carrying
`added_at` and `added_by`. Migrate the existing links across without losing
them. Then write one query returning each tag with its task count, ordered
desc, in a single DB round trip.
**Interview angle:** `through` models are the standard "do you actually know
M2M" probe, and migrating an existing M2M to a through model is a genuine
production scenario.

### Drill 4
1. Which side does the FK column live on, and why?
2. `select_related` vs `prefetch_related` — mechanism, not just "use for FK".
3. `on_delete=CASCADE` vs `PROTECT` vs `SET_NULL` — pick one for a real case
   and defend it.
4. Why does filtering across a reverse relation duplicate rows?
5. `task.project` vs `task.project_id` — which one hits the database?

---

## Phase 5 — Django Admin ✅ notes (ch9)

- [x] `createsuperuser`, `/admin/`
- [x] registering models, `admin.site.register` vs `@admin.register`
- [x] `list_display`, `list_filter`, `search_fields`
- [x] `__str__` as the admin's label
- [x] `list_select_related` and the admin N+1
- [ ] `inlines` (`TabularInline` / `StackedInline`)
- [ ] `fieldsets`, `readonly_fields`, `prepopulated_fields`
- [ ] custom admin **actions** (bulk operations)
- [ ] overriding `get_queryset` to scope what a user sees
- [ ] `list_editable`, `date_hierarchy`, `autocomplete_fields`

### Assignment 5a (easy)
Add a `TaskInline` to `ProjectAdmin` so tasks are editable inside a project.
Add a computed `is_overdue` column to `list_display` (a method, green/red via
`boolean=True`).
**Interview angle:** inlines are the first thing asked in "how far have you
customised the admin?" A computed column shows you know `list_display` takes
callables.

### Assignment 5b (med-hard)
Add a bulk admin action "mark selected as done" that runs in **one UPDATE
query** and reports how many rows changed via `message_user`. Then create a
staff (non-superuser) group that can view tasks but not delete them, and
override `get_queryset` so that group only sees tasks from projects they own.
**Interview angle:** row-level permission scoping via `get_queryset` is a real
architecture question, and "admin action in a single query" tests whether you
reach for `.update()` instead of a Python loop with `.save()`.

### Drill 5
1. How does Django know about `tasks/admin.py`? Nothing imports it.
2. A FK in `list_display` — what's the hidden cost and the fix?
3. `is_staff` vs `is_superuser` vs permissions vs groups.
4. Why is the admin not a substitute for an API?
5. How would you stop a support agent from seeing other customers' rows?

---

## Python Interlude II — functions, decorators, generators

- [ ] `*args` / `**kwargs`, positional-only and keyword-only params
- [ ] scope: LEGB, `nonlocal`, `global`
- [ ] closures — and the late-binding-in-a-loop trap
- [ ] first-class functions, `lambda`, `sorted(key=...)`
- [ ] decorators, with and without arguments; `functools.wraps`
- [ ] iterators vs iterables vs generators; `yield`
- [ ] generator expressions and laziness (this *is* the QuerySet idea)
- [ ] context managers: `with`, `__enter__`/`__exit__`, `contextlib`
- [ ] `map` / `filter` / `zip` / `enumerate` / `any` / `all`

### Assignment P-II-a (easy) — `practice/pii-a-decorators/`
Write three decorators: `@timer` (logs duration), `@retry(times=3)` (takes an
argument), and `@memoize` (caches by args). Then compare yours with
`functools.lru_cache`.
**Interview angle:** "write a decorator that retries" is asked verbatim, all
the time. The argument-taking one trips most people — it's a decorator factory,
one extra layer of nesting.

### Assignment P-II-b (med-hard)
Build a log-file pipeline out of **generators only** — read lines, parse,
filter errors, aggregate by hour — that processes a 1 GB file in constant
memory. Prove memory stays flat. Then write a `@contextmanager`-based timer
and explain when you'd use it over the decorator.
**Interview angle:** "how do you process a file too big for RAM?" The answer is
generators, and this is exactly why Django QuerySets are lazy and why
`.iterator()` exists. Ties Python core straight back to the ORM.

### Drill P-II
1. What does a decorator actually *do* to the function it wraps?
2. Why `functools.wraps`? What breaks without it?
3. Generator vs list comprehension — memory and reusability.
4. Explain the loop-variable closure trap and two fixes.
5. `yield` vs `return`. What is `yield from`?

---

## Phase 6 — Request lifecycle, middleware, CBVs

- [ ] the full request→response path, in order
- [ ] middleware: order, `__call__`, short-circuiting, writing one
- [ ] `HttpRequest` / `HttpResponse` anatomy
- [ ] function-based vs class-based views; `as_view()`
- [ ] generic CBVs (`ListView`, `DetailView`) and the MRO/mixin pattern
- [ ] sessions and cookies

### Assignment 6a (easy)
Write a middleware that logs method, path, status and duration for every
request. Register it and verify ordering by adding a second one.
**Interview angle:** "write a middleware" is the standard Django-specific
coding task. Ordering (request goes top-down, response comes bottom-up) is the
follow-up everyone fumbles.

### Assignment 6b (med-hard)
Extend it into a request-ID middleware: generate a UUID per request, attach it
to `request`, include it in every log line **and** in a response header, using
`contextvars` so it's available deep in the call stack without passing it
around. Then add a middleware that short-circuits and returns 429 after N
requests/minute per IP.
**Interview angle:** request-ID/correlation-ID propagation is a real
distributed-systems question, and `contextvars` is the grown-up answer to
thread-locals. Rate limiting tests whether you know middleware can return
early without calling `get_response`.

### Drill 6
1. Name the stages of the request/response cycle in order.
2. Middleware A above B — who sees the request first? The response?
3. How does `as_view()` turn a class into a callable view?
4. FBV vs CBV — when do you actually reach for a CBV?
5. Where does Django put session data by default?

---

## Phase 7 — Django REST Framework

- [ ] why DRF exists; installing, `INSTALLED_APPS`
- [ ] `Serializer` vs `ModelSerializer`
- [ ] validation: field-level, `validate_<field>`, `validate()`
- [ ] nested serializers, `depth`, `SerializerMethodField`
- [ ] `APIView` → generics → `ViewSet` → `ModelViewSet` (the ladder)
- [ ] routers and generated URLs
- [ ] pagination, filtering, ordering, search
- [ ] renderers, parsers, content negotiation, versioning
- [ ] throttling

### Assignment 7a (easy)
Full CRUD for `Task` via `ModelViewSet` + router. Nest the project as an
object on read but accept a plain id on write. Add pagination.
**Interview angle:** read/write asymmetry in serializers is the #1 DRF
question. The answer is `to_representation` or separate read/write
serializers via `get_serializer_class`.

### Assignment 7b (med-hard)
Add: `?status=&project=&due_before=` filtering, a custom `validate()` rejecting
a `due_date` in the past on create but allowing it on update, a
`SerializerMethodField` for `subtask_count` **without introducing an N+1**
(annotate in `get_queryset`), and a custom action `POST /api/tasks/{id}/done/`.
**Interview angle:** four separate interview questions in one task. The N+1 in
a `SerializerMethodField` is the trap — it's invisible until you count queries.

### Drill 7
1. `Serializer` vs `ModelSerializer` — when would you refuse the Model one?
2. Where do you put validation involving two fields?
3. `ViewSet` vs `ModelViewSet` vs `APIView` — the ladder, and what each buys.
4. How do you avoid an N+1 inside a serializer?
5. How does DRF decide the response format?

---

## Python Interlude III — OOP & the object model

- [ ] classes, `__init__`, `self`, class vs instance attributes
- [ ] inheritance, `super()`, multiple inheritance, **MRO / C3**
- [ ] mixins — the pattern Django is built on
- [ ] dunder methods: `__str__`, `__repr__`, `__eq__`, `__hash__`, `__len__`
- [ ] `@property`, `@classmethod`, `@staticmethod`
- [ ] `__slots__`, `dataclasses`
- [ ] duck typing, `abc`, protocols
- [ ] exceptions: custom classes, hierarchy, `else`/`finally`
- [ ] type hints, `Optional`, `Generic`, and what `mypy` does

### Assignment P-III-a (easy) — `practice/piii-a-shapes/`
A small class hierarchy with an abstract base, `@property` for computed values,
`__repr__` and `__eq__` on every class. Make instances usable in a `set` (so:
`__hash__` too).
**Interview angle:** `__eq__` without `__hash__` silently makes objects
unhashable — a favourite gotcha. Also `__str__` vs `__repr__`, asked constantly.

### Assignment P-III-b (med-hard)
Build a mini ORM: a `Model` base class where subclasses declare `Field()`
attributes, and the base collects them (via `__init_subclass__` or a
metaclass), validates on `__init__`, and generates `CREATE TABLE` SQL. Add a
`.save()` that prints the INSERT.
**Interview angle:** this is *literally how Django models work*. Building a toy
version means you can answer "what does `models.Model` actually do?" and
"what's a metaclass?" — the deepest Python question that gets asked — from
experience rather than recitation.

### Drill P-III
1. What is the MRO and how does Python compute it? Diamond inheritance?
2. `@classmethod` vs `@staticmethod` — a real use for each.
3. `__str__` vs `__repr__` — who calls which?
4. If you define `__eq__`, what else must you define and why?
5. What is a metaclass, in one sentence, and when have you needed one?

---

## Phase 8 — Auth, custom user, permissions, JWT

- [ ] `django.contrib.auth`: `User`, groups, permissions
- [ ] **custom user model** — and why it must be done before the first migrate
- [ ] `AbstractUser` vs `AbstractBaseUser`
- [ ] password hashing, `make_password`, hashers
- [ ] session auth vs token auth vs JWT — the real tradeoffs
- [ ] `simplejwt`: access/refresh, rotation, blacklisting
- [ ] DRF permission classes; object-level permissions
- [ ] `request.user`, `AnonymousUser`

### Assignment 8a (easy)
Add JWT login/refresh with `djangorestframework-simplejwt`. Lock the task
endpoints to authenticated users. Add `owner` FK to `Task`, set from
`request.user` on create.
**Interview angle:** "how do you set a field from the request user?" → in
`perform_create`, never trusting a client-supplied `owner`. That's a security
question wearing a DRF costume.

### Assignment 8b (med-hard)
Write a custom permission `IsOwnerOrReadOnly` and scope `get_queryset` so users
only ever see their own tasks. Then add a role system (via groups) where a
"manager" sees their whole team's tasks. Prove with tests that user A gets 404
(not 403) for user B's task — and explain why 404 is the better answer.
**Interview angle:** object-level permissions + the 403-vs-404 information-leak
question. Senior-level signal.

### Drill 8
1. Why must a custom user model exist before the first `migrate`? What if it doesn't?
2. `AbstractUser` vs `AbstractBaseUser`.
3. Session auth vs JWT — pick one for a mobile app and defend it.
4. How do you invalidate a JWT before it expires?
5. Authentication vs authorization, in DRF terms — which class does which?

---

## Phase 9 — Query optimization, indexes, transactions

- [ ] `EXPLAIN ANALYZE` from Django, `django-debug-toolbar`
- [ ] indexes: `db_index`, `Meta.indexes`, composite, partial
- [ ] when an index is *not* used
- [ ] `select_for_update`, row locks
- [ ] `transaction.atomic` — decorator, context manager, nesting, savepoints
- [ ] `ATOMIC_REQUESTS`
- [ ] connection pooling, `CONN_MAX_AGE`
- [ ] isolation levels and the classic anomalies

### Assignment 9a (easy)
Seed 100k tasks. Time a `filter(status=...)`. Add an index. Time it again.
Read the `EXPLAIN` output before and after.
**Interview angle:** "how do you know an index helped?" — you must be able to
read a sequential scan vs an index scan.

### Assignment 9b (med-hard)
Simulate a double-booking race: two concurrent transactions assigning the same
task. Show the bug, then fix it two ways — `select_for_update` and an optimistic
`F()`-based version check — and explain the tradeoff. Wrap in `atomic` and show
what a nested `atomic` does on the inner rollback.
**Interview angle:** concurrency is where senior interviews go. Pessimistic vs
optimistic locking with a working demo puts you ahead of most candidates.

### Drill 9
1. When does adding an index make things *worse*?
2. `select_for_update` — what exactly is locked, and until when?
3. Nested `atomic` blocks — inner fails, outer continues. What happened?
4. What is `CONN_MAX_AGE` and why does it matter under load?
5. You're told "the API got slow." Walk through your diagnosis.

---

## Phase 10 — Testing

- [ ] `TestCase` vs `TransactionTestCase` vs `SimpleTestCase`
- [ ] `pytest-django`, fixtures, `conftest.py`
- [ ] `APIClient`, authenticating in tests
- [ ] factories (`factory_boy`) vs fixtures
- [ ] mocking: `unittest.mock`, `patch`, where to patch
- [ ] `assertNumQueries`
- [ ] coverage, and why the number lies

### Assignment 10a (easy)
Test the task CRUD endpoints: happy path, 401 unauthenticated, 404 for another
user's task, 400 on invalid payload.
**Interview angle:** "what do you test in an API?" — the four cases above is a
complete answer.

### Assignment 10b (med-hard)
Add a factory for `Task`/`Project`/`User`. Write a regression test using
`assertNumQueries` that fails if anyone reintroduces the N+1 from 7b. Mock an
external call so the test never touches the network.
**Interview angle:** `assertNumQueries` as a *regression guard* is an answer
almost nobody gives to "how do you prevent performance regressions?"

### Drill 10
1. `TestCase` vs `TransactionTestCase` — what's the rollback difference?
2. Where do you patch — where it's defined or where it's used? Why?
3. Factories vs fixtures.
4. How do you test something time-dependent?
5. 100% coverage and still broken. How?

---

## Python Interlude IV — concurrency, GIL, async

- [ ] the GIL: what it does and doesn't protect
- [ ] threading vs multiprocessing vs asyncio — and when each wins
- [ ] `concurrent.futures`
- [ ] `async` / `await`, event loop, coroutines
- [ ] blocking calls inside async code — the classic footgun
- [ ] Django async views, `sync_to_async` / `async_to_sync`
- [ ] memory: reference counting, cycles, `gc`

### Assignment P-IV-a (easy) — `practice/piv-a-fetch/`
Fetch 20 URLs three ways — sequential, `ThreadPoolExecutor`, `asyncio` — and
time each. Then do the same for a CPU-bound task and watch threads fail to help.
**Interview angle:** *the* GIL question, answered with your own measurements.
"Threads don't help CPU-bound work in CPython" is much stronger when you've
seen the numbers.

### Assignment P-IV-b (med-hard)
Write an async worker pool with bounded concurrency (`asyncio.Semaphore`),
per-task timeout, retry with backoff, and graceful cancellation on Ctrl-C.
Then break it on purpose with a blocking `time.sleep` inside a coroutine and
explain what you observe.
**Interview angle:** bounded concurrency + cancellation is the realistic async
question. The deliberate blocking-call bug is the thing interviewers most want
you to recognise.

### Drill P-IV
1. What is the GIL, and what problem does it exist to solve?
2. I/O-bound vs CPU-bound — which concurrency model for each?
3. What happens if you call a blocking function in an async view?
4. `asyncio.gather` vs `TaskGroup` — error handling difference.
5. Why is multiprocessing expensive, and how does data cross processes?

---

## Phase 11 — Caching, signals, background jobs

- [ ] cache backends; Redis in Docker (same detour as Postgres)
- [ ] per-view, per-site, low-level `cache.get/set`
- [ ] cache invalidation strategies, key design, stampede
- [ ] signals: `post_save`, `pre_delete`, custom — and why they're often a mistake
- [ ] Celery: broker, worker, task, retry, idempotency
- [ ] `django-celery-beat` for schedules
- [ ] `transaction.on_commit` — the signal/Celery race

### Assignment 11a (easy)
Redis in `docker-compose.yml`. Cache the task-list endpoint. Invalidate on
save via a signal. Measure the before/after.
**Interview angle:** "how would you cache this endpoint?" plus the immediate
follow-up, "how do you invalidate it?"

### Assignment 11b (med-hard)
Move an email-on-task-complete to Celery. Make it idempotent, give it retry
with backoff, and fire it from `transaction.on_commit` — then demonstrate the
bug you get *without* `on_commit` (worker reads a row that isn't committed yet).
**Interview angle:** the `on_commit` race is a genuine production war story and
a fantastic thing to be able to tell. Idempotency is the standard follow-up to
any queue question.

### Drill 11
1. Two hard things in computer science — how do you actually invalidate?
2. Why do signals make code hard to follow? What's the alternative?
3. A Celery task fires on `post_save` and can't find the row. Why?
4. At-least-once delivery — what must your task guarantee?
5. Cache stampede: what is it, how do you prevent it?

---

## Phase 12 — Security

- [ ] CSRF: the attack, and what Django's token does
- [ ] XSS and template autoescaping; when `|safe` bites
- [ ] SQL injection — why the ORM is safe and `raw()`/`extra()` aren't
- [ ] `SECRET_KEY`, what it signs, rotation
- [ ] `DEBUG=True` in prod — exactly what leaks
- [ ] `ALLOWED_HOSTS`, host-header attacks
- [ ] CORS vs CSRF (people conflate these)
- [ ] clickjacking, HSTS, secure cookies
- [ ] mass assignment via serializer `fields = "__all__"`

### Assignment 12a (easy)
Run `python manage.py check --deploy`. Fix every warning. Write down what each
one actually protects against.
**Interview angle:** a real checklist, and `check --deploy` is a great thing to
name-drop.

### Assignment 12b (med-hard)
Demonstrate three vulnerabilities against your own app, then fix them: (1) a
SQL injection via a `raw()` query with string formatting, (2) mass assignment
letting a user set `owner` or `is_staff` through a `"__all__"` serializer,
(3) IDOR — reading another user's task by guessing the id.
**Interview angle:** IDOR and mass assignment are the two most common real API
vulnerabilities. Having exploited them yourself makes the answer concrete.

### Drill 12
1. Explain CSRF to someone who thinks CORS prevents it.
2. Why is the ORM injection-safe? When does that break?
3. `DEBUG=True` in production — walk through what an attacker gets.
4. What does `SECRET_KEY` sign, and what breaks if it rotates?
5. What is IDOR and how do you structurally prevent it?

---

## Phase 13 — Settings, env, deployment

- [ ] split settings (base/dev/prod) vs one file with env switches
- [ ] 12-factor config, secrets handling
- [ ] `collectstatic`, WhiteNoise, media vs static
- [ ] gunicorn/uvicorn, workers vs threads, sizing them
- [ ] Dockerfile for Django; multi-stage build
- [ ] running `migrate` on deploy — and why not in the app container
- [ ] logging config, structured logs
- [ ] health checks, readiness vs liveness

### Assignment 13a (easy)
Dockerfile for the app; extend `docker-compose.yml` so `web` + `db` come up
together with one command. No `runserver` — gunicorn.
**Interview angle:** "how do you containerise Django?" `runserver` in a
Dockerfile is an instant red flag.

### Assignment 13b (med-hard)
Split settings into `base/dev/prod`, drive everything from env vars, add
WhiteNoise + `collectstatic` in a multi-stage build, and write a deploy script
that runs migrations as a separate step before rolling the app. Document what
happens if two app instances start simultaneously and both run `migrate`.
**Interview angle:** concurrent migrations on deploy is a sharp
infrastructure question that separates "I've deployed" from "I've deployed at
scale."

### Drill 13
1. Where do secrets live, and why not in `settings.py`?
2. gunicorn workers vs threads — how do you size them?
3. Why run `migrate` outside the app container?
4. Static vs media files — who serves each in production?
5. Your deploy doubled p99 latency. First three things you check?

---

## Phase 14 — Capstone: Task Manager API

Everything above, in one coherent project, built from an empty app so nothing
is copy-paste.

- [ ] models with proper constraints and indexes
- [ ] full DRF API: CRUD, filtering, pagination, nested reads
- [ ] JWT auth, object-level permissions
- [ ] Celery for notifications, Redis for caching
- [ ] test suite with factories and `assertNumQueries` guards
- [ ] dockerised, env-driven, `check --deploy` clean
- [ ] a README that explains the *decisions*, not the commands

### Assignment 14 — the portfolio piece
Ship it, then write a one-page design doc: the data model and why, the three
biggest tradeoffs you made, and what you'd change at 100× the traffic.
**Interview angle:** this is the project you walk them through. The design doc
is what turns "I built a CRUD app" into a system-design conversation you
control.

---

## Interview-readiness checklist (final pass)

- [ ] I can explain the request lifecycle end to end, no notes
- [ ] I can find and fix an N+1 and *prove* it with query counts
- [ ] I can add a non-null column to a populated table with zero downtime
- [ ] I can write a decorator, a generator pipeline, and a context manager cold
- [ ] I can explain the GIL and pick the right concurrency model
- [ ] I can explain the MRO and why Django is built on mixins
- [ ] I can defend session vs JWT for a given product
- [ ] I can name what `check --deploy` protects against
- [ ] I have one project I can walk through for 20 minutes
- [ ] I have three war stories: a bug, a performance fix, a tradeoff
