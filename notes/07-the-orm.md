# Chapter 7 — The ORM

`python manage.py shell` = a Python REPL with settings + apps already loaded.
That's why `from tasks.models import Task` works there and fails in bare
`python`. Use it to test queries without building an endpoint first.

`Task.objects` is the **manager** — the entry point for every query.

## Create

```python
t = Task(title="Learn the ORM")   # in memory only, no SQL yet
t.save()                          # the INSERT
Task.objects.create(title="x")    # shorthand: build + save
```

`t.id` is `None` until `save()` — Postgres assigns it, Django reads it back.

**Defaults are applied by Python, not the DB.** `status` became `"todo"`
before the INSERT ran; the column itself has no `DEFAULT`.

## Read

```python
Task.objects.all()
Task.objects.filter(status="done")      # WHERE
Task.objects.exclude(status="done")     # WHERE NOT
Task.objects.get(id=1)                  # exactly one
```

**`get()` vs `filter()`** — the classic trap:

| | Returns | If 0 matches | If 2+ matches |
|---|---|---|---|
| `filter()` | QuerySet | empty QuerySet | all of them |
| `get()` | the object | raises `DoesNotExist` | raises `MultipleObjectsReturned` |

Rule: `get()` only for something unique (usually the pk). `filter()` otherwise.

## Field lookups — the `__` syntax

Anything beyond exact equality is `field__lookup`:

```python
Task.objects.filter(title__icontains="chapter")
Task.objects.filter(due_date__isnull=True)
```

| Lookup | SQL |
|---|---|
| `__exact` (default) | `=` |
| `__iexact` | `=` case-insensitive |
| `__contains` / `__icontains` | `LIKE %x%` / `ILIKE` |
| `__startswith` / `__endswith` | `LIKE x%` / `%x` |
| `__in` | `IN (...)` |
| `__gt` `__gte` `__lt` `__lte` | `>` `>=` `<` `<=` |
| `__range` | `BETWEEN` |
| `__isnull` | `IS NULL` |
| `__date` `__year` `__month` | date parts |

Multiple kwargs are `AND`: `filter(status="todo", due_date__isnull=False)`.

## KEY CONCEPT — QuerySets are lazy

```python
qs = Task.objects.all()
qs = qs.filter(status="todo")
qs = qs.exclude(title__icontains="x")
qs = qs.order_by("-created_at")
# still ZERO queries so far
```

Nothing hits the database until the result is actually needed. Those four calls
collapse into **one** SQL statement.

**What triggers it:** iterating, `list()`, `len()`, slicing, `bool()`, printing
in the shell.

Inspect the SQL Django built:

```python
print(qs.query)
```

**GOTCHA:** `print(qs.query)` interpolates the values for display — the real
query uses placeholders with params sent separately. So it isn't runnable SQL,
and it's also why the ORM is not SQL-injectable.

Also notice it selects **every** column — that's what `.only()` / `.values()`
are for later.

## Update — two ways

```python
t = Task.objects.get(id=1)         # object way
t.status = "done"
t.save()                           # auto_now fires

Task.objects.filter(id=1).update(status="todo")   # bulk way
```

| | Queries for N rows | `auto_now` / custom `save()` / signals |
|---|---|---|
| loop + `.save()` | N | run |
| `.update()` | 1 | **skipped** |

`.update()` goes straight to SQL. Fast but dumb. Returns the rows-changed count.

`t.refresh_from_db()` — reload a stale in-memory object after a bulk update.

## Delete

```python
Task.objects.filter(title="x").delete()   # no need to fetch first
t.delete()                                # or on one object
```

Returns a tally of what was removed.

## Frequently used — cheatsheet

```python
Task.objects.count()                       # SELECT COUNT(*)
Task.objects.exists()                      # cheaper than count() for a yes/no
Task.objects.first()  /  .last()           # one object or None
Task.objects.order_by("-created_at")       # "-" = DESC
Task.objects[:10]                          # LIMIT 10 (slicing is lazy too)
Task.objects.distinct()

Task.objects.values("id", "title")         # dicts, not model objects
Task.objects.values_list("title", flat=True)   # a flat list of values
Task.objects.only("title")                 # fetch fewer columns
```

```python
Task.objects.get_or_create(title="x", defaults={"status": "todo"})
Task.objects.update_or_create(...)
Task.objects.bulk_create([Task(title="a"), Task(title="b")])   # one INSERT
```

**OR queries** need `Q`; **comparing two columns** needs `F`:

```python
from django.db.models import Q, F, Count, Avg

Task.objects.filter(Q(status="todo") | Q(status="done"))   # | = OR, & = AND
Task.objects.filter(updated_at__gt=F("created_at"))        # column vs column
Task.objects.aggregate(Avg("id"))                          # one summary dict
Task.objects.values("status").annotate(n=Count("id"))      # GROUP BY status
```

## Gotchas to remember

- defaults and `choices` are enforced in **Python**, not the database
- `.update()` skips `auto_now`, custom `save()` and signals
- `get()` raises; `filter()` doesn't
- QuerySets are lazy — but each *new* QuerySet re-queries
- `print(qs.query)` is for reading, not for running
