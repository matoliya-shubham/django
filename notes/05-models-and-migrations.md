# Chapter 5 — Models and Migrations

A **model** = one Python class = one database table. Class attributes are the
columns. Code lives in `tasks/models.py`.

**JS:** this is my `schema.prisma` model — except it's real Python, and the
class I write *is* the thing I query with. No codegen step.

`class Task(models.Model)` — that parenthesis is `extends`. Inheriting is what
gives me `.save()`, `Task.objects.all()` and migrations for free.

## The 3 gotchas

**1. `null` vs `blank` — the classic trap**

| | Level | Means |
|---|---|---|
| `null=True` | database | column accepts `NULL` |
| `blank=True` | validation | forms/admin accept empty |

Rule: **never `null=True` on a string field.** A text column already has an
empty value (`""`). Allowing `NULL` too gives two ways to say "nothing".
Dates have no empty string, so `due_date` needs both.

**2. `choices` is not a DB constraint.** It gives dropdowns and validation
only. Postgres just sees `varchar(20)`. Raw SQL can write garbage.

**3. `auto_now_add` vs `auto_now`** — once on INSERT vs every `.save()`.
Both run in Python, so a bulk `.update()` skips `updated_at` silently.

Also: Django adds the `id` primary key itself, and `__str__` (Python's
`toString()`) never appears in migrations — migrations are **schema only**.

## makemigrations ≠ migrate

| Command | Does | Prisma |
|---|---|---|
| `makemigrations` | writes a Python file. **No DB access at all.** | `migrate dev --create-only` |
| `migrate` | runs the SQL | `migrate deploy` |

Django doesn't diff against the live DB. It replays the existing files in
`tasks/migrations/` to build the expected schema, then diffs `models.py`
against that. **The migration files are the source of truth, not the database.**

## The generated file

`tasks/migrations/0001_initial.py` — three keys:

- `initial = True` — nothing comes before it
- `dependencies` — migrations are a **DAG**, not a line
- `operations` — the payload (`CreateModel`, `AddField`, `AlterField`, …)

It's a **Python object, not SQL**. One file, translated per backend at run
time — Chapter 6 shows the same file producing two different `CREATE TABLE`s.

## Commands

```bash
python manage.py makemigrations tasks     # generate      (no DB needed)
python manage.py sqlmigrate tasks 0001    # preview SQL   (needs DB)
python manage.py showmigrations           # [X] vs [ ]    (needs DB)
```

`showmigrations` needs a connection because the applied list lives *in* the
database, in `django_migrations`.

Table names come out as `<app>_<model>` → `tasks_task`.

Next: Chapter 6 stands up real Postgres before running `migrate`.
