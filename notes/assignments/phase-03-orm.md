# Phase 3 Assignments — The ORM

> What I was asked to build, what I got wrong, and why.

---

## Assignment 3a — a `report` command

**The task:** build `python manage.py report`. It prints how many tasks are in
each status, which tasks are overdue today, and the 5 most recently updated.
All the counting must be done by the database, not by Python loops.

**Where the code is:** `tasks/management/commands/report.py`.

### Management commands — the folder rules

```
tasks/
└── management/
    ├── __init__.py          ← BOTH of these are required
    └── commands/
        ├── __init__.py
        └── report.py        →  python manage.py report
```

The **file name becomes the command name**. Django finds commands by walking
through every app in `INSTALLED_APPS` and looking for `management/commands/*.py`.

> **The mistake I made:** I created `commands/__init__.py` but **not**
> `management/__init__.py`. Without it, that folder is not a Python package, so
> Django skips it **without saying anything**. You just get
> `Unknown command: 'report'` and no clue why.

```python
class Command(BaseCommand):          # the class MUST be called Command
    help = "..."                     # shown by `manage.py help report`
    def handle(self, *args, **options): ...
```

**Use `self.stdout.write()`, not `print()`.**

`BaseCommand` keeps `stdout` as an attribute. That lets a test swap in a fake
one and capture the output:

```python
call_command("report", stdout=out)
```

With `print` the text goes straight to the terminal and the test cannot see it.
Same reason for `self.style.SUCCESS` — it adds colour in a terminal and plain
text when the output is piped somewhere.

### `annotate` vs `aggregate` — the main idea of Phase 3

```python
Task.objects.values("status").annotate(count=Count("id"))
# → SELECT status, COUNT(id) FROM tasks_task GROUP BY status
```

**`values()` goes before `annotate()`, and it sets the `GROUP BY`.**

That is the whole trick, and it reads backwards from what you would expect. Swap
them around and you get something completely different — a count stuck onto each
individual row.

| | gives you | SQL |
|---|---|---|
| `aggregate(Count("id"))` | **a dictionary** — one answer for the whole queryset | `SELECT COUNT(id)` |
| `annotate(count=Count("id"))` | **a queryset** — one answer per group | `... GROUP BY ...` |

"How many tasks in total?" → `aggregate`.
"How many tasks per status?" → `annotate`.

One number, versus one number *each*.

### Smaller things I learned

- `filter(due_date__lt=today).exclude(status="done")` becomes **one** query:
  `WHERE due_date < ... AND NOT status = 'done'`. Chaining does not mean more
  trips to the database.
- Use `timezone.now().date()`, not `datetime.date.today()`. It respects the
  `USE_TZ` setting.
- `.order_by(...)` **replaces** `Meta.ordering`. It does not add to it.
- Slicing with `[:5]` becomes SQL `LIMIT 5`. The database sends 5 rows. Nothing
  is fetched and then thrown away.
- I typed `f"\Recent"` meaning `\n`. `\R` is not a real escape sequence, and
  Python does not error — it just keeps the backslash. (Python 3.12+ gives a
  `SyntaxWarning`.)

### What I discovered: `choices` is NOT a database rule

My own report printed a status of `ddd`. That value is not in `STATUS_CHOICES`.
It was in my database anyway.

**`choices` is only information for validation.** The admin builds a dropdown
from it. `ModelForm` checks against it. DRF builds a `ChoiceField` from it.
**Postgres knows nothing about it.**

So this saves without complaint:

```python
Task.objects.create(title="x", status="ddd")
```

**`.save()` does not call `.full_clean()`.** Django keeps "write to the database"
and "validate this" as two separate jobs on purpose. Validation belongs to the
form layer. Anything that skips forms — the shell, a data migration, a Celery
task, `bulk_create` — writes whatever you give it.

> **This is a standard interview question: "does `choices` validate?" Most people
> say yes.** It does not.

To make the database enforce it (this also closes the `Meta.constraints` topic
left over from Phase 2):

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            condition=models.Q(status__in=[c[0] for c in STATUS_CHOICES]),
            name="task_status_valid",
        )
    ]
```

Now `status="ddd"` raises `IntegrityError` **no matter who writes it**.

**Two traps while adding it:**

1. **`check=` was removed in Django 6.0** (deprecated in 5.1). The option is now
   called **`condition=`**.
2. **The migration failed** until I cleaned up the existing `ddd` row. Postgres
   checks a new CHECK constraint against the data already in the table before it
   accepts it.

   Same lesson as 2b, from the other direction: **you cannot add a rule to data
   that already breaks it.** In a real project that cleanup is a `RunPython` in
   one migration, with the constraint in the next.

### A Python gotcha: class bodies do not nest

```python
class Task(models.Model):
    STATUS_CHOICES = [...]
    class Meta:
        constraints = [... [c[0] for c in STATUS_CHOICES] ...]   # NameError!
```

`class Meta` sits inside `class Task`, so it *looks* nested. But **class bodies
are not closures.** While `Meta`'s body is running, `Task`'s body is just another
namespace being built. It is not in `Meta`'s search path.

(`Task.STATUS_CHOICES` does not work either. The `Task` class object does not
exist yet — you are still inside the statement that creates it.)

Python looks names up in this order: **Local, Enclosing, Global, Builtin**
(LEGB). Notice what is missing: **class scope**. It is skipped on purpose.

That is also why this classic fails:

```python
class A:
    xs = [1, 2, 3]
    ys = [x * 2 for x in xs]        # fine — xs is the iterable, evaluated outside
    zs = [x * len(xs) for x in xs]  # NameError — xs used inside the comprehension
```

**The fix:** move the constant to **module level**. That is global scope, which
*is* in the LEGB chain, so both class bodies can see it.

### Bulk update skips everything

```python
Task.objects.filter(status="ddd").update(status="todo")
```

This is one `UPDATE ... WHERE` in the database. It never loads the objects into
Python.

So it is fast — but it also **skips `save()`, skips signals, and skips
`auto_now`**. My `updated_at` did not change. That is the trade-off you accept
for a bulk operation.

---

## Assignment 3b — prove the query count does not grow

**The task:** the report must run in a fixed number of queries no matter how much
data there is. And I have to **prove** it.

### How to count queries

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    ...
self.stdout.write(f"{len(ctx)} queries")
```

`ctx.captured_queries` holds the actual SQL text. That is how you find out
*which* query is repeating.

It lives in `django.test.utils` but works fine outside tests. In Phase 10 there
is `assertNumQueries`, which turns this into a test that **fails** if someone
adds an N+1 later. That is how a fix stays fixed.

### `.count()` vs `len(qs)` — the result cache

I started at 5 queries. Swapping one `.count()` for `len()` made it 4.

| | SQL it runs | does it keep the rows? |
|---|---|---|
| `.count()` | `SELECT COUNT(*)` | **no** — so the loop after it queries again |
| `len(qs)` | `SELECT ...` the actual rows | **yes** — the loop reuses them, 0 extra |

A QuerySet keeps a **result cache**. `len()` forces it to fetch and fills that
cache. `.count()` deliberately fetches no rows, so it has nothing to cache.

> **Rule: if you are going to loop over it anyway, use `len()`. If you only want
> the number, use `.count()`.**

**When does a QuerySet actually run?** (Drill 3, Q1)

It runs on: looping over it, `len()`, `list()`, `bool()`, slicing *with a step*,
and pickling.

It does **not** run on: `.count()`, `.exists()`, or plain slicing. Those send
their own separate SQL instead.

### Making the N+1 appear

Printing `task.project` inside the loop took me from 4 queries to 6.

Here is why. The task row only stores `project_id` — a number. The project's name
is not in there. So the moment I ask for `task.project`, Django has to go and
fetch it. **Once per task.**

```
give me the recent tasks       → 1 query
what is project 7?  (task A)   → 1
what is project 2?  (task B)   → 1
                                 (task C has no project → no query)
```

**1 query for the list, plus N more for the items. That is why it is called
"N+1".** I had 3 tasks and got 2 extra queries, because one task had no project.

> **An analogy:** you need ten ingredients, so you drive to the shop ten separate
> times. `select_related` is writing a list and going once.

Other things to know:

- Django does **not** reuse the result. Each task object caches its own project.
  So ten tasks on the same project still cost ten queries.
- **How to spot it:** the same SQL repeating, with only the id changing. That is
  the fingerprint. It is what you look for in `django-debug-toolbar` or in query
  logs.
- You will never notice it with 3 rows. With 500 it is 501 queries and an 8
  second page. It works fine in development and falls over in production.

### The fix

```python
Task.objects.select_related("project").order_by("-updated_at")[:5]
```

`select_related` makes it one query with a `JOIN`. The task columns and the
project columns come back together, so `task.project` is already filled in.

Chain it before the slice. (The order of `filter`, `order_by` and
`select_related` does not matter — nothing runs until the queryset is evaluated.
But the slice has to be last, because slicing closes the queryset off.)

| | use it for | SQL |
|---|---|---|
| `select_related` | ForeignKey, OneToOne — **one** related object | one query with a `JOIN` |
| `prefetch_related` | ManyToMany, reverse FK — **many** related objects | **two** queries, matched up in Python |

A many-to-many cannot be joined without repeating every task row once per tag.
So `prefetch_related("tags")` fetches all the tags in a second query and matches
them up in Python. **That is 2 queries, not 1 — but it is still a fixed number.**

Knowing which of the two to reach for is the follow-up to every N+1 question.

### The proof

```python
Task.objects.bulk_create([Task(title=f"seed {i}", status="todo", project=p)
                          for i in range(1000)])
```

**I went from 2 tasks to 1002 tasks. The query count was 5 before and 5 after.**

That is the proof: the number of queries does not depend on the amount of data.

`bulk_create` sends **one** `INSERT` with 1000 rows, instead of 1000 separate
trips. Two things it does not do, and both get asked:

- **It does not call `save()`**, so no `pre_save`/`post_save` signals fire, and
  any custom `save()` code is skipped.
- On most databases it does not fill in the new `id`s. **Postgres is the
  exception** — it can, using `RETURNING`.

### One honest catch

My `[:5]` slice **caps** the damage. However big the table gets, the N+1 can only
ever add 5 extra queries here.

Where it really explodes is a list with **no limit**. A view that renders all
1002 tasks and prints `task.project.name` would run 1003 queries. Same bug, but
with no ceiling.

---

## Still open for Phase 3

- [ ] `values()` / `values_list()` / `only()` / `defer()`
- [ ] `bulk_update`, `iterator()`
- [ ] **Drill 3**

---

## Drill 3 — scored 3/5 (retest Q2, Q4, Q5)

### Q1. When does a QuerySet actually run? ✅

> *I said:* iteration, `len()`, `list()`. Correct.

The other half is what does **not** run it, because that is where the surprises
are.

```python
qs = Task.objects.filter(status="todo")   # no SQL yet
qs = qs.exclude(title="x")                # still none
qs = qs.order_by("-created_at")           # still none
for t in qs:                              # NOW it runs — one query
```

Chaining builds the query. It does not send it. That is why
`.filter().exclude()` is one trip, not two.

These send their own SQL and return a plain value, so they do **not** fill the
cache:

- `.count()` → `SELECT COUNT(*)`
- `.exists()` → `SELECT 1 ... LIMIT 1`
- plain slicing `[:5]` → adds `LIMIT 5`, still lazy

So this is **two** queries, not one — I hit exactly this in 3b:

```python
if qs.count() > 0:     # query 1
    for t in qs:       # query 2
```

Triggers I did not name: `bool(qs)` (so `if qs:`), `repr(qs)` (which is why
typing a queryset in the shell seems to run it), and pickling.

### Q2. `filter().filter()` vs `filter(a, b)` ❌ I said "same"

True for ordinary fields:

```python
Task.objects.filter(status="todo", title__icontains="x")
Task.objects.filter(status="todo").filter(title__icontains="x")
# identical: WHERE status = 'todo' AND title ILIKE '%x%'
```

**Not true across a relation where there can be many related rows** (many-to-many
or reverse FK).

```python
# A: one filter — ONE task must be todo AND have "learn" in its title
Project.objects.filter(tasks__status="todo", tasks__title__icontains="learn")

# B: two filters — one task is todo, a DIFFERENT task has "learn"
Project.objects.filter(tasks__status="todo").filter(tasks__title__icontains="learn")
```

**I ran it. A gave 1. B gave 1001.**

> **The rule:**
> **one `.filter()` = one join** → all conditions must be met by **the same**
> related row.
> **separate `.filter()`s = separate joins** → **different** rows can satisfy each.

(Note: `filter(tags__name="a", tags__name="b")` is not even valid Python —
`SyntaxError: keyword argument repeated`. The demo needs two *different* fields
on the same relation.)

### The bigger catch hiding in that result: joins duplicate rows

**1001 was not 1001 projects.** I do not have 1001 projects. Those were duplicate
rows.

A JOIN returns one row per matching *combination*. B joins the task table twice,
so a project with 1000 todo tasks and 1 "learn" task produces 1000 identical
rows.

```python
Project.objects.filter(...).filter(...).count()              # 1001 — rows
Project.objects.filter(...).filter(...).distinct().count()   # the real answer
```

> **Rule: filtering across a multi-valued relation duplicates rows. You almost
> always want `.distinct()`.**

This causes a very specific real bug: a list page suddenly shows the same item
three times after someone adds a filter on a related model.

**Full answer to give:**

> For ordinary fields they are identical. Across a multi-valued relation they
> differ: one `filter()` is one join and every condition must be met by the same
> related row; separate `filter()`s are separate joins, so different rows can
> satisfy each one. Either way the join duplicates rows, so add `.distinct()`.

### Q3. `annotate` vs `aggregate` ✅

> *I said:* "annotate gives per-row, aggregate gives one total." Correct.

The precision to add is the **return type**, because it decides what you can do
next:

| | returns | can you chain `.filter()` after it? |
|---|---|---|
| `aggregate(...)` | **a dict** — the queryset is finished | no |
| `annotate(...)` | **a queryset** | yes |

That chaining is the real power — you can filter on the value you just computed:

```python
Project.objects.annotate(n=Count("tasks")).filter(n__gt=5)
# → HAVING COUNT(tasks.id) > 5
```

Django turns a filter on an annotation into SQL **`HAVING`**, not `WHERE`.
("What is the difference between WHERE and HAVING" is a common SQL question —
this is where it shows up in Django.)

**Trap, straight from Q2:** counting across two joins double-counts.

```python
Project.objects.annotate(n=Count("tasks"))                   # inflated
Project.objects.annotate(n=Count("tasks", distinct=True))    # correct
```

Same fan-out that gave me 1001. `Count` counts joined rows.

### Q4. What is `F()` for? ❌ did not know

**The problem.** Adding 1 to a counter the obvious way:

```python
task = Task.objects.get(pk=1)
task.views = task.views + 1
task.save()
```

That is three steps: **read**, **add in Python**, **write back**.

Two requests at the same moment:

```
A reads views = 10
B reads views = 10        ← both read before either writes
A writes 11
B writes 11               ← should be 12
```

**One increment disappeared.** This is a **lost update**. It happens under load,
at random, and never while you are watching.

**The fix — let the database do the arithmetic:**

```python
from django.db.models import F
Task.objects.filter(pk=1).update(views=F("views") + 1)
```

```sql
UPDATE tasks_task SET views = views + 1 WHERE id = 1
```

The value never comes into Python. The database reads and writes in **one atomic
statement** and locks the row while doing it. Both requests run it, and the
answer is 12.

**So what is `F()`?** It means "the current value of this column, in the
database" — a reference to the column instead of a Python value. It also lets you
compare two columns:

```python
Task.objects.filter(updated_at__gt=F("created_at"))   # edited after creation
```

Without `F()` you would have to load every row and compare in Python.

**Gotcha:** after an `F()` update the Python object is stale. `task.views` still
holds the old number until `refresh_from_db()`.

**One-line answer:**

> `F()` refers to a column's value inside the database. It turns
> read-modify-write into a single atomic UPDATE, which fixes the lost-update race
> when two requests change the same row at once.

### Q5. `get()` raises on zero and on many ❌ did not know the names

`.get()` promises **exactly one** row. Two ways that breaks:

| situation | exception |
|---|---|
| **zero** rows match | `Task.DoesNotExist` |
| **two or more** match | `Task.MultipleObjectsReturned` |

Both are generated automatically on every model. I met the first in Assignment 1b.

```python
try:
    task = Task.objects.get(pk=task_id)
except Task.DoesNotExist:
    return JsonResponse({"error": "not found"}, status=404)
except Task.MultipleObjectsReturned:
    raise      # the data broke an assumption — do not hide it
```

> **People catch the first and forget the second.** And the second means
> something is genuinely wrong: you believed a field was unique and it is not.
> Swallowing it buries a data bug.

Two alternatives:

```python
Task.objects.filter(pk=task_id).first()   # None if nothing — no exception
get_object_or_404(Task, pk=task_id)       # raises Http404 → an HTML page
```

- `.first()` — when "not found" is normal and expected.
- `.get()` — when not-found is an error.
- `get_object_or_404` — for HTML pages. **Not** for a JSON API, which is exactly
  why I hand-rolled the 404 in 1b.
