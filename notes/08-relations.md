# Chapter 8 — Relations (ForeignKey)

## What a relation is

A relation stores a **link to a row in another table** instead of copying its
data. Without it I'd repeat the project name on every task — and renaming the
project would mean updating every row, with nothing stopping the two from
drifting apart.

So: store the project **once**, and have each task point at it by id. The
database then enforces that the pointer is valid.

## The three types

| Field | Shape | Lives on | Example |
|---|---|---|---|
| `ForeignKey` | one-to-many | the **many** side | a Task belongs to one Project; a Project has many Tasks |
| `OneToOneField` | one-to-one | either side | a Profile extends one User |
| `ManyToManyField` | many-to-many | either side | a Task has many Tags; a Tag has many Tasks |

- **ForeignKey** — by far the most common. Owner, category, author, parent.
- **OneToOne** — splitting a table, usually to add fields to a model someone
  else wrote (`User`).
- **ManyToMany** — Django silently creates a hidden **join table** for it.

**JS:** same as Prisma's `@relation`. The difference is Django generates the
reverse accessor for me automatically.

One `Project` has many `Task`s. The FK always lives on the **many** side.

```python
class Project(models.Model):          # must be defined ABOVE Task
    name = models.CharField(max_length=100)

class Task(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True, blank=True,
    )
```

`null=True` so existing rows have something valid to hold — otherwise
`makemigrations` stops and asks what to backfill.

## Migration 0002 — the DAG becomes visible

```python
dependencies = [("tasks", "0001_initial")]
```

`0001` had `[]` and `initial = True`. Now the chain is explicit, so ordering
never depends on filenames.

`sqlmigrate` shows the `ALTER TABLE` adds three things:

- the column **`project_id`**
- a real **FOREIGN KEY constraint**
- an **index** on it (FKs get one automatically — you filter on them constantly)

Unlike `choices`, this one **is** enforced by Postgres.

## Why `project_id`?

Django appends `_id` to the FK column, because the column stores an integer
while the Python attribute gives an object.

```python
t.project      # the Project object   (may hit the DB)
t.project_id   # just the integer     (never hits the DB)
```

Use `project_id` when all you need is the id — it's free.

## Both directions

```python
t.project          # forward: Task -> Project
p.tasks.all()      # reverse: Project -> Tasks
```

`Project` has no `tasks` field — `related_name="tasks"` created that accessor.
Without it the default is `p.task_set.all()`.

## `__` also spans relationships

```python
Task.objects.filter(project__name="Django Learning")
Project.objects.filter(tasks__status="done")
Task.objects.filter(project__name__icontains="django")   # chains further
```

Django writes the `INNER JOIN`. Same `__` as field lookups — it just walks the
relation first.

## KEY CONCEPT — the N+1 problem

```python
for t in Task.objects.all():
    print(t.project.name)
# 3 tasks -> 4 queries. 1000 tasks -> 1001 queries.
```

1 query for the list, then 1 more per row to fetch its project. **The most
common Django performance bug**, and invisible locally with 3 rows.

Fix:

```python
Task.objects.select_related("project")    # -> 1 query
```

| | Use for | How |
|---|---|---|
| `select_related` | ForeignKey / OneToOne (forward) | one query, SQL JOIN |
| `prefetch_related` | reverse FK / ManyToMany | two queries, joined in Python |

Count queries with `reset_queries()` + `len(connection.queries)`
(`from django.db import connection, reset_queries`).

## `on_delete` — mandatory, and destructive by default

| | Deleting the Project… |
|---|---|
| `CASCADE` | deletes its tasks too |
| `PROTECT` | raises, refuses |
| `SET_NULL` | keeps tasks, sets `project` to `NULL` (needs `null=True`) |
| `RESTRICT` | like PROTECT, unless something else cascades it |

Django requires this argument because it won't guess something that
destructive. **I watched `CASCADE` wipe all 3 tasks with one
`Project.objects.all().delete()`.** For a real app `PROTECT` or `SET_NULL` is
usually safer.

Django runs the cascade **itself, in Python** — it doesn't rely on Postgres.
That's why `PROTECT` and `SET_NULL` can exist; they aren't SQL features.

## Frequently used — cheatsheet

```python
# create
t = Task.objects.create(title="x", project=p)
p.tasks.create(title="x")            # from the parent, project set for me

# read
t.project            # forward, the object
t.project_id         # forward, just the int (free)
p.tasks.all()        # reverse
p.tasks.count()
p.tasks.filter(status="done")        # reverse manager takes any queryset call

# filter across the relation
Task.objects.filter(project__name="Django Learning")
Task.objects.filter(project__isnull=True)        # orphans
Task.objects.filter(project__in=[p1, p2])
Project.objects.filter(tasks__status="done").distinct()   # distinct! joins duplicate rows

# performance
Task.objects.select_related("project")           # FK forward   -> 1 query
Project.objects.prefetch_related("tasks")        # reverse/M2M  -> 2 queries

# aggregate over the relation
from django.db.models import Count
Project.objects.annotate(n=Count("tasks"))       # each project + its task count
Project.objects.filter(tasks__isnull=True)       # projects with no tasks
```

ManyToMany only (`task.tags`):

```python
task.tags.add(tag)        # link
task.tags.remove(tag)     # unlink
task.tags.set([t1, t2])   # replace all
task.tags.clear()         # unlink everything
```

**Watch `.distinct()`** — filtering across a reverse relation joins rows, so a
project with 3 matching tasks comes back 3 times without it.

## Gotchas

- restart `manage.py shell` after editing models — Python caches imports and
  won't hot-reload (`runserver` does, the shell doesn't)
- the FK goes on the "many" side, always
- `related_name` is optional but always worth setting
- `CASCADE` is the copy-paste default everywhere; think before keeping it
