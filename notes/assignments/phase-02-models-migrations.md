# Phase 2 Assignments — Models, Migrations, Postgres

> What the task was, what I got wrong, and why.

---

## Assignment 2a — Tag, M2M, `Meta.ordering`

**Task:** `Tag` model (`name`, unique), a `ManyToManyField` from `Task`, read
the generated **join table** in DBeaver before migrating, and `Meta.ordering`
so newest tasks come first.

**Shipped:** `tasks/models.py` — `Tag`, `Task.tags`, `Task.Meta.ordering`.
Migrations `0003`, `0004`.

### Mistakes I actually made

**1. Wrote a `ForeignKey` where a `ManyToManyField` was asked for.**

A FK puts a `tag_id` **column** on the task row — one column, one value. So a
task could have exactly one tag. A task tagged both `urgent` *and* `backend` is
impossible.

| | meaning |
|---|---|
| `ForeignKey(Tag)` | each task has **one** tag — that's a *category* |
| `ManyToManyField(Tag)` | each task has **many** tags — that's *tags* |

Also: `on_delete` isn't valid on a M2M. There's no column on either table to
cascade *from* — the relating lives entirely in the third table.

**2. `null=True` on the M2M** → `fields.W340: null has no effect on
ManyToManyField`. Which column would the NULL go in? "No tags" isn't a null,
it's **zero rows in the join table**. Keep `blank=True` — that's form
validation, a different layer (`null` = database, `blank` = validation).

**3. `related_name='tags'` on `Task.tags`** → reverse read as `tag.tags.all()`,
"the tags of a tag".

> **Rule:** `related_name` is the plural of **the model you're coming back to**.
> From a `Tag` I want `tag.tasks.all()`, so `related_name="tasks"`.

**4. Pasted the `through=` example into the `Tag` model.** `Tag` and `TaskTag`
are two different models — `Tag` = "a tag that exists", `TaskTag` = "*this* task
wearing *that* tag". Also three `NameError`s: a class body executes top to
bottom at import, so a name must already exist when referenced. That's exactly
why Django accepts `"Task"` as a **string** in `ForeignKey`/`through`.

### The payoff: how Django models a M2M

`makemigrations` only says `AddField(... ManyToManyField ...)` — the join table
is implicit. `sqlmigrate` shows the truth:

```sql
CREATE TABLE "tasks_task_tags" (
    "id"      bigint PRIMARY KEY,
    "task_id" bigint NOT NULL,   -- → tasks_task
    "tag_id"  bigint NOT NULL    -- → tasks_tag
);
ALTER TABLE "tasks_task_tags" ADD CONSTRAINT ... UNIQUE ("task_id", "tag_id");
CREATE INDEX ... ON "tasks_task_tags" ("task_id");
CREATE INDEX ... ON "tasks_task_tags" ("tag_id");
```

**Interview answer:** *a third, hidden table holding two foreign keys.* Nothing
changes on either original table.

- `UNIQUE(task_id, tag_id)` → `task.tags.add(t)` twice is a **no-op**, verified:
  count stayed at 2. Contrast `objects.create()`, which happily duplicates.
- Both FK columns get an index — joins run in both directions.
- `-- (no-op)` under "Change Meta options": **`ordering` emits zero SQL.** It's
  enforced by Django when building the query, not by Postgres.
- `BEGIN; ... COMMIT;` — the whole migration is one transaction. **Transactional
  DDL** is a Postgres feature; **MySQL lacks it**, so a failed migration there
  can strand the schema half-applied. Good answer to "what's the risk of
  migrations in prod?"

### `Meta` — settings about the model, not fields

```python
class Meta:
    ordering = ["-created_at"]      # "-" = descending, same as .order_by()
```

Applies to **every** query — `Task.objects.all()`, `project.tasks.all()`, the
admin list, DRF pagination — with no `.order_by()` anywhere.

- **It's a performance footgun.** Every query now pays for an `ORDER BY`. On a
  big table with no index on `created_at`, that's a sort on every read.
- `ordering` is Django-level; `db_table`, `unique_together`, `constraints`,
  `indexes` **are** schema and do produce real SQL.

### `through=` — when the relationship itself carries data

The follow-up to the M2M question: *"what if you need to know who added the tag,
and when?"* You can't add a column to a table Django owns, so you promote the
join table to a real model:

```python
class TaskTag(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("task", "tag")]

class Task(models.Model):
    tags = models.ManyToManyField(Tag, through="TaskTag", related_name="tasks")
```

Three consequences — the reason it gets asked:

1. **You now own the constraints.** The auto table gave `UNIQUE(task_id, tag_id)`
   for free; yours doesn't, hence the explicit `unique_together`.
2. **`.add()` gets restricted** — Django can't invent values for required extra
   fields. Use `TaskTag.objects.create(...)` or `through_defaults={...}`.
3. **Adding `through` later is painful** — Django sees it as dropping one M2M and
   creating another, so the auto table (and its data) is dropped. In production
   that's a three-migration dance: create new table, `RunPython` to copy, drop
   old.

### Migration state vs schema — the thing that surprised me

Changing `related_name` produced `0004_alter_task_tags.py` whose SQL is **empty**.

Migration files are a **replay of model definitions**, not a schema diff. Each
rebuilds Django's in-memory picture of the models, so anything in a field's
definition — `related_name`, `choices`, `verbose_name`, `help_text`,
`validators` — is recorded even though Postgres never hears about it.

**Why it must be complete:** a later `RunPython` calls `apps.get_model()` to get
the model *as it was at that point in history*. That only works if state was
tracked all along. So **don't delete "pointless" no-SQL migrations** — the state
drifts and later migrations break.

---

## Assignment 2b — add a non-null column to a populated table

**Task:** `Project.slug`, `null=False`, `unique=True`, on a table that already
has rows. **Three migrations.**

*The* classic migrations interview question — "zero-downtime non-null column".

| # | migration | what |
|---|---|---|
| 1 | `0005_project_slug` | add `slug`, `null=True` → existing rows get NULL |
| 2 | `0006_backfill_project_slugs` | `RunPython` fills every slug from `name` |
| 3 | `0007_alter_project_slug` | alter to `null=False, unique=True` |

You cannot do it in one: Postgres refuses to add a NOT NULL column with no
default to a table that already has rows — what would it put there?

### Mistakes I actually made

**1. `name=True` when I meant `null=True`.** `name` is a *real* Django field
kwarg (it overrides the field's attribute name), so Django doesn't reject it —
it tries to use `True` as a column name. Silent-wrong, same family as the
`id:` dict-key bug in Phase 1.

**2. Left `unique=True` on in step 1.** That collapses the dance and skips the
lesson. **Constraint last, after the data is proven clean.** If two projects
share a name, leaving unique on means finding out *mid-`RunPython`* with the
migration half-run, instead of cleanly at step 3 on a table I can inspect.

> Subtlety: Postgres treats NULLs as distinct, so a unique index actually
> tolerates many NULLs — step 1 might have slipped through. The collision only
> explodes at backfill time. Worse, not better.

**3. Deleting a migration file.** Safe here **only because it was unapplied**.

> **Rule:** unapplied = free to delete and regenerate. Applied = must be
> reversed first. Deleting an applied migration leaves its row in
> `django_migrations` pointing at a file that no longer exists.

### The data migration

```bash
python manage.py makemigrations tasks --empty --name backfill_project_slugs
```

Django can't generate this — it has no idea what belongs in those columns.

```python
def backfill_slugs(apps, schema_editor):
    Project = apps.get_model("tasks", "Project")      # NOT a normal import
    seen = set()
    for project in Project.objects.all().order_by("pk"):
        base = slugify(project.name) or f"project-{project.pk}"
        slug, n = base, 2
        while slug in seen:
            slug = f"{base}-{n}"
            n += 1
        seen.add(slug)
        project.slug = slug
        project.save(update_fields=["slug"])

operations = [migrations.RunPython(backfill_slugs, migrations.RunPython.noop)]
```

**`apps.get_model("tasks", "Project")` — the rule everyone breaks.**
`from tasks.models import Project` gives the model as it is *today*. This
migration may run on a fresh DB in six months, when `Project` has four fields
that don't exist yet at this point in history → the import references columns
the table doesn't have. `apps.get_model()` returns the **historical** model,
rebuilt from migration state as of 0006.

- `slugify(name) or f"project-{pk}"` — `slugify("***")` returns `""`, a valid
  non-null value that would then collide with every other empty one. Python's
  `or` returns the first truthy operand (same as JS `||`).
- The `while slug in seen` loop — `slugify` isn't injective. Two "Website
  Redesign" projects both give `website-redesign`; the second becomes
  `website-redesign-2`. Without this, step 3 fails.
- `update_fields=["slug"]` — UPDATE touches one column, not every field. Matters
  on big tables, and avoids clobbering concurrent writes to other columns.
- `migrations.RunPython.noop` as `reverse_code` — "reversible, but nothing to
  undo". **Omit the second argument and the migration is irreversible**, so
  `migrate tasks 0005` would refuse.

### Step 3 — and why this is an interview question

```sql
ALTER TABLE "tasks_project" ALTER COLUMN "slug" SET NOT NULL;
ALTER TABLE "tasks_project" ADD CONSTRAINT ..._uniq UNIQUE ("slug");
CREATE INDEX ..._like ON "tasks_project" ("slug" varchar_pattern_ops);
```

- **`SET NOT NULL`** takes an `ACCESS EXCLUSIVE` lock — **every read and write
  blocks** while Postgres scans to prove no NULL exists. PG12+ escape hatch: add
  a validated `CHECK (slug IS NOT NULL)` first, then `SET NOT NULL` is instant
  because the check already proved it.
- **`ADD CONSTRAINT ... UNIQUE`** builds a unique index, blocking **writes** for
  the whole build. Zero-downtime version: `CREATE UNIQUE INDEX CONCURRENTLY`,
  then `ADD CONSTRAINT ... USING INDEX`. Django exposes `AddIndexConcurrently` —
  and `CONCURRENTLY` **cannot run inside a transaction**, so that migration needs
  `atomic = False`.
- One transaction again → safe, but locks are held until `COMMIT`. **Safety and
  lock duration trade against each other.**
- The `varchar_pattern_ops` index is just Django making `slug__startswith` fast.

**Full answer to give:**

> Three migrations: add nullable, backfill with `RunPython`, then add the
> constraint. On a large table the third step still locks — so add NOT NULL via
> a validated CHECK, and build the unique index `CONCURRENTLY` outside a
> transaction.

---

## Commands used

```bash
python manage.py makemigrations tasks
python manage.py sqlmigrate tasks 0003              # see the real SQL — ALWAYS do this
python manage.py makemigrations tasks --empty --name backfill_project_slugs
python manage.py showmigrations tasks               # [X] applied / [ ] pending
python manage.py migrate
```

`sqlmigrate` is the habit worth keeping. The migration file hides the join
table; the SQL doesn't hide anything.

---

## Still open for Phase 2

- [ ] `Meta`: `db_table`, `unique_together` / `constraints`
- [ ] how to safely reverse / squash a migration
- [ ] **Drill 2**

---

## Drill 2 — 5/5 core answers, depth was the gap

All five correct. What was missing each time was the **consequence** the
interviewer probes for. Recording those.

### Q1. `null=True` vs `blank=True` ✅

> *Said:* "null=True is db level, blank=True is validation." Correct.

**Follow-up — "when would you use both?"** Together is right for genuinely
optional data (`due_date`). But on **string fields, avoid `null=True`**: "no
value" then has two representations, `""` and `NULL`, so every query needs
`Q(x="") | Q(x__isnull=True)`. Use `blank=True` alone and let empty mean `""` —
which is exactly what `description` does.

> **`null` is the database column; `blank` is forms and validation. They're not
> two halves of one switch.**

### Q2. Where does `default=` get applied? ✅ Python, at save

**The consequence:** Django does **not** put a `DEFAULT` on the column. `status`
has `default="todo"` but the Postgres column has no default. So anything writing
outside the Django model gets nothing:

```sql
INSERT INTO tasks_task (title) VALUES ('x');   -- status is NULL, not 'todo'
```

Raw SQL, reporting jobs, another service on the same DB, a `psql` session. "Our
defaults don't apply when the data team bulk-loads" is a real bug with this cause.

- **During migrations it's temporary.** Adding a field with a `default` to a
  populated table makes Django set a real DB default so existing rows get a
  value — then **drop it again** in the same migration. Which is also why
  `default` can't rescue the 2b dance: there the value is *computed per row*.
- **`default=list`, not `default=[]`** — pass the callable, uncalled. `[]`
  evaluates once at import and every row shares one list: the `def f(x=[])` trap
  in Django clothing. Django blocks this one with a system check.

### Q3. Two people ran `makemigrations` ✅ diagnosed, resolution was missing

> *Said:* "two 0008 files with same dependency." Right — now *fix* it.

**Mental model:** migrations are a **DAG**, not a list. Each file declares
`dependencies`. A valid graph has **one leaf**. Two files on `0007` = two leaves:

> `Conflicting migrations detected; multiple leaf nodes in the migration graph`

**1. Mine isn't applied or pushed** (common) — delete my `0008`, pull theirs,
re-run `makemigrations`. Mine regenerates as `0009` on top. Cleanest, no artifact.

**2. Both already shared** — can't delete history others have run:

```bash
python manage.py makemigrations --merge
```

Writes `0009_merge_...` with **no operations**, depending on both `0008`s. One
leaf again.

**Caveat:** `--merge` only works when the changes are **independent**. Different
fields, fine. Same field altered twice, or the same table renamed — the graph
merges and then the operations fight. Resolve by hand.

### Q4. `django_migrations` ✅ "deleting a row makes Django rerun it"

**The second half:** it reruns against a database where **the SQL already
happened**:

```
ProgrammingError: column "slug" of relation "tasks_project" already exists
```

> The filesystem and the database each hold half the truth; this table is the
> **join** between them. Django trusts the ledger, not the schema.

Hence `--fake`:

```bash
python manage.py migrate tasks 0007 --fake    # write/remove the row, run NO SQL
```

"Trust me, the schema is already in this state." The right tool when the halves
have genuinely drifted; a great way to make it much worse if you're wrong.

Same reason deleting an **applied** migration file is dangerous (hit this in
2b): the row stays, pointing at a file that's gone.

### Q5. Rolling back in production ✅ mechanically

> *Said:* "migrate back to the previous migration number." → `migrate tasks 0006`.

The question said **production**, i.e. "and what goes wrong?"

1. **Not everything is reversible.** `RunPython` with no `reverse_code` refuses
   outright — hence `RunPython.noop` in 2b. Same for `RunSQL`.
2. **Reversible ≠ lossless.** Reversing `AddField` **drops the column**. The
   slug data is gone; rolling forward again gives an empty column. Reversibility
   is about *structure* only.
3. **Rolling back is rarely what you want.** Schema and code deploy separately,
   and down-migrations are almost never tested.

> **Roll forward, not back.** Write a new migration that corrects the problem.
> Reverse only when the migration is recent, isolated, and you've checked what
> data it destroys.

**The practice that avoids needing it:** make migrations **backward-compatible
with the currently-running code** — add columns before the code uses them, stop
using a column before dropping it. **Expand/contract.** Then a code rollback
never requires a schema rollback, which is the situation actually worth fearing.
