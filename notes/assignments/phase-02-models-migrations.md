# Phase 2 Assignments — Models, Migrations, Postgres

> What I was asked to build, what I got wrong, and why.

---

## Assignment 2a — tags, the hidden join table, and ordering

**The task:** add a `Tag` model with a unique `name`. Link it to `Task` with a
`ManyToManyField`. Look at the generated **join table** in DBeaver before
migrating. Add `Meta.ordering` so the newest task comes first.

**Where the code is:** `tasks/models.py`. Migrations `0003` and `0004`.

### Mistakes I actually made

**1. I used a `ForeignKey` where a `ManyToManyField` was asked for.**

A ForeignKey adds a `tag_id` **column** to the task row. One column holds one
value. So a task could have exactly one tag.

Could a task be tagged both `urgent` *and* `backend`? No. Not possible.

| | what it means |
|---|---|
| `ForeignKey(Tag)` | each task has **one** tag — that is a *category* |
| `ManyToManyField(Tag)` | each task has **many** tags — that is *tags* |

Also, `on_delete` is not allowed on a many-to-many. There is no column on either
table to cascade from. All the linking happens in a third table.

**2. I put `null=True` on the many-to-many.**

Django warned me: `fields.W340: null has no effect on ManyToManyField`.

Think about it — which column would the NULL go in? There isn't one. "No tags"
is not a null. It is **zero rows in the join table**.

I kept `blank=True`, which is different. That one is about form validation.
(`null` = database, `blank` = validation.)

**3. I wrote `related_name='tags'` on `Task.tags`.**

`related_name` is the name you use coming back *from the other side*. So that
gave me `tag.tags.all()` — "the tags of a tag". Nonsense.

> **Rule:** `related_name` is the plural of **the model you are coming back to**.
> From a `Tag` I want `tag.tasks.all()`, so it is `related_name="tasks"`.

**4. I pasted the `through=` example into the `Tag` model.**

`Tag` and `TaskTag` are two different models:

- `Tag` = "a tag that exists"
- `TaskTag` = "*this* task wearing *that* tag"

I also got three `NameError`s. A class body runs top to bottom when the file is
imported, so a name has to already exist when you use it.

That is exactly why Django lets you write `"Task"` as a **string** in
`ForeignKey` and `through`. The string is looked up later, once everything is
defined.

### The payoff — how Django really does many-to-many

The migration file only says `AddField(... ManyToManyField ...)`. The join table
is hidden. `sqlmigrate` shows what actually happens:

```sql
CREATE TABLE "tasks_task_tags" (
    "id"      bigint PRIMARY KEY,
    "task_id" bigint NOT NULL,   -- points at tasks_task
    "tag_id"  bigint NOT NULL    -- points at tasks_tag
);
ALTER TABLE "tasks_task_tags" ADD CONSTRAINT ... UNIQUE ("task_id", "tag_id");
CREATE INDEX ... ON "tasks_task_tags" ("task_id");
CREATE INDEX ... ON "tasks_task_tags" ("tag_id");
```

**The interview answer, in one line:** *a third, hidden table holding two foreign
keys.* Neither original table changes at all.

Four things worth remembering from that SQL:

- **`UNIQUE(task_id, tag_id)`** means adding the same tag twice does nothing. I
  tested it: `t.tags.add(urgent)` a second time, and the count stayed at 2.
  Compare `objects.create()`, which happily makes duplicates.
- **Both foreign key columns get an index.** You join in both directions, so both
  need one.
- **`-- (no-op)`** appears where my `Meta.ordering` change should be. So
  `ordering` produces **no SQL at all**. Django applies it when building the
  query. Postgres never hears about it.
- **`BEGIN; ... COMMIT;`** — the whole migration is one transaction. If step 3
  fails, steps 1 and 2 are undone. This is called **transactional DDL**. Postgres
  has it. **MySQL does not**, so a failed migration there can leave the schema
  half-changed. Good answer to "what is risky about migrations in production?"

### `Meta` — settings about the model, not fields

```python
class Meta:
    ordering = ["-created_at"]    # "-" means descending, same as .order_by()
```

This applies to **every** query: `Task.objects.all()`, `project.tasks.all()`, the
admin list, DRF pagination. No `.order_by()` needed anywhere.

Two things to know:

- **It can hurt performance.** Every query now has an `ORDER BY`. On a big table
  with no index on `created_at`, every read pays for a sort.
- `ordering` is a Django-only thing. But `db_table`, `unique_together`,
  `constraints` and `indexes` **are** real schema and do produce real SQL.

### `through=` — when the link itself needs to store data

The follow-up question: *"what if you need to know who added the tag, and when?"*

You cannot add a column to a table Django owns. So you take the join table over
and make it a real model:

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

Three consequences, which is why it gets asked:

1. **You now own the rules.** Django's hidden table gave you
   `UNIQUE(task_id, tag_id)` for free. Yours does not, so you write
   `unique_together` yourself.
2. **`.add()` stops being simple.** Django cannot invent values for your extra
   required fields. So you create the row yourself with
   `TaskTag.objects.create(...)`, or pass `through_defaults={...}`.
3. **Switching to `through` later is painful.** Django sees it as deleting one
   many-to-many and creating another. The old table is dropped, and its data
   with it. In production that means three migrations: make the new table, copy
   the rows with `RunPython`, drop the old one.

### Migration *state* vs the actual schema — this surprised me

Changing `related_name` created `0004_alter_task_tags.py`. Its SQL is **empty**.

Why? Migration files are a **replay of your model definitions**, not a diff of
the database. Each file rebuilds Django's mental picture of your models. So
anything in a field definition gets recorded — `related_name`, `choices`,
`verbose_name`, `help_text`, `validators` — even though Postgres never sees it.

**Why that picture has to be complete:** a later `RunPython` calls
`apps.get_model()` to get a model *as it was at that moment in history*. That
only works if every change was recorded along the way.

> So do **not** delete "pointless" migrations that produce no SQL. The picture
> drifts and later migrations break.

---

## Assignment 2b — adding a NOT NULL column to a table that already has rows

**The task:** add `Project.slug`. It must end up `null=False` and `unique=True`.
But `Project` already has rows with no slug. This takes **three migrations**.

This is *the* classic migrations interview question.

| # | migration | what it does |
|---|---|---|
| 1 | `0005_project_slug` | add `slug` as `null=True`, so existing rows get NULL |
| 2 | `0006_backfill_project_slugs` | `RunPython` fills in every slug from `name` |
| 3 | `0007_alter_project_slug` | change it to `null=False, unique=True` |

You cannot do it in one step. Postgres will not add a NOT NULL column with no
default to a table that already has rows — what would it put in them?

### Mistakes I actually made

**1. I typed `name=True` when I meant `null=True`.**

And `name` is a *real* Django field option. It overrides the field's attribute
name. So Django did not reject it. It tried to use `True` as a column name.

Same family of bug as the unquoted `id:` dictionary key in Phase 1: wrong, but
silent.

**2. I left `unique=True` on in step 1.**

That squashes three steps into two and skips the whole lesson.

> **The rule: add the constraint last, once the data is known to be clean.**

If two projects happen to share a name, leaving `unique` on means I find out
*in the middle of the backfill*, with the migration half-finished. Instead of
cleanly at step 3, on a table I can inspect first.

(Subtle detail: Postgres treats each NULL as different from every other NULL. So
a unique index actually allows many NULLs, and step 1 might have slipped
through. The collision would then explode at backfill time. Worse, not better.)

**3. I deleted a migration file.**

Safe here — but **only because it had not been applied yet**.

> **Rule: not applied = safe to delete and regenerate. Already applied = must be
> reversed first.**

Deleting a migration that *has* run leaves its row in `django_migrations`
pointing at a file that no longer exists.

### The data migration

```bash
python manage.py makemigrations tasks --empty --name backfill_project_slugs
```

Django cannot write this one. It has no idea what belongs in those columns.

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

`from tasks.models import Project` gives you the model as it is **today**. But
this migration might run on a fresh database in six months, when `Project` has
four new fields. At *this point in history* those columns do not exist yet, so
the import would ask for columns that are not there.

`apps.get_model()` gives you the **historical** model, rebuilt from the
migration state as of migration 0006.

The smaller pieces:

- `slugify(name) or f"project-{pk}"` — `slugify("***")` returns an empty string.
  Empty string is a perfectly valid non-null value, and then every such project
  collides. The `or` catches that. (Python's `or` returns the first truthy value,
  just like `||` in JS.)
- The `while slug in seen` loop — `slugify` is not unique. Two projects called
  "Website Redesign" both give `website-redesign`. The second becomes
  `website-redesign-2`. Without this, step 3 fails.
- `update_fields=["slug"]` — the UPDATE touches one column instead of all of
  them. Faster on big tables, and it will not overwrite other columns that
  someone else changed at the same time.
- `migrations.RunPython.noop` as the reverse — meaning "reversible, but there is
  nothing to undo". **If you leave the second argument out, the migration becomes
  irreversible** and `migrate tasks 0005` will refuse to run.

### Step 3, and why this is an interview question

```sql
ALTER TABLE "tasks_project" ALTER COLUMN "slug" SET NOT NULL;
ALTER TABLE "tasks_project" ADD CONSTRAINT ..._uniq UNIQUE ("slug");
CREATE INDEX ..._like ON "tasks_project" ("slug" varchar_pattern_ops);
```

**`SET NOT NULL`** takes an `ACCESS EXCLUSIVE` lock. That means **every read and
every write to the table blocks** while Postgres scans it to prove there are no
NULLs. On Postgres 12+ there is a way around it: first add a validated
`CHECK (slug IS NOT NULL)`, then `SET NOT NULL` is instant, because the check
already proved it.

**`ADD CONSTRAINT ... UNIQUE`** builds a unique index, and that blocks **writes**
for as long as the build takes. The zero-downtime version is
`CREATE UNIQUE INDEX CONCURRENTLY`, then attach it with
`ADD CONSTRAINT ... USING INDEX`. Django exposes this as `AddIndexConcurrently`.
And `CONCURRENTLY` **cannot run inside a transaction**, so that migration needs
`atomic = False`.

It is all one transaction again. That is safe, but it also means the locks are
held until the final `COMMIT`. **Safety and lock time pull against each other.**

(The `varchar_pattern_ops` index is just Django making `slug__startswith` fast.
Harmless.)

**The full answer to give:**

> Three migrations: add it nullable, backfill with `RunPython`, then add the
> constraint. On a big table the third step still locks — so add NOT NULL via a
> validated CHECK, and build the unique index `CONCURRENTLY`, outside a
> transaction.

---

## Commands I used

```bash
python manage.py makemigrations tasks
python manage.py sqlmigrate tasks 0003              # see the real SQL — always do this
python manage.py makemigrations tasks --empty --name backfill_project_slugs
python manage.py showmigrations tasks               # [X] applied, [ ] pending
python manage.py migrate
```

`sqlmigrate` is the habit worth keeping. The migration file hid the join table.
The SQL hides nothing.

---

## Drill 2 — 5/5 on the main answers, depth was the gap

All five were right. What I was missing each time was the **consequence** the
interviewer digs for. Those are recorded here.

### Q1. `null=True` vs `blank=True` ✅

> *I said:* "null=True is db level, blank=True is validation." Correct.

**Follow-up — "when would you use both?"**

Both together is right for data that is genuinely optional, like `due_date`.

But on **text fields, avoid `null=True`**. Otherwise "empty" has two different
forms, `""` and `NULL`, and every query has to check both:
`Q(x="") | Q(x__isnull=True)`. Use `blank=True` on its own and let empty always
mean `""`. That is exactly what `description` does.

> **`null` is about the database column. `blank` is about forms and validation.
> They are not two halves of the same switch.**

### Q2. Where does `default=` get applied? ✅ In Python, when saving

**The consequence I missed:** Django does **not** put a `DEFAULT` on the column.

`status` has `default="todo"`, but the Postgres column has no default on it. So
anything that writes without going through the Django model gets nothing:

```sql
INSERT INTO tasks_task (title) VALUES ('x');   -- status is NULL, not 'todo'
```

Raw SQL, reporting jobs, another service sharing the database, a `psql` session.
"Our defaults do not apply when the data team bulk-loads" is a real bug with
exactly this cause.

- **During a migration it is temporary.** Adding a field with a `default` to a
  table that has rows makes Django put a real database default on, so existing
  rows get a value — and then **drop it again** in the same migration. That is
  also why `default` cannot rescue the 2b dance: there the value has to be
  *computed per row*.
- **Write `default=list`, not `default=[]`.** Pass the function, do not call it.
  `[]` is evaluated once when the file is imported, and then every row shares the
  same list. That is the `def f(x=[])` trap from Python Interlude I, in Django
  clothing. Django blocks this one with a system check.

### Q3. Two people both ran `makemigrations` ✅ diagnosed, but no fix given

> *I said:* "two 0008 files with the same dependency." Right. Now how do I fix it?

**The mental model:** migrations are a **graph**, not a list. Each file says what
it depends on. A valid graph has exactly **one** newest file. Two files both
depending on `0007` means two "newest" files, and Django refuses:

> `Conflicting migrations detected; multiple leaf nodes in the migration graph`

**Case 1 — mine is not applied and not pushed** (the usual case). Delete my
`0008`, pull theirs, run `makemigrations` again. Mine regenerates as `0009` on
top of theirs. Cleanest — no extra file.

**Case 2 — both are already shared.** I cannot delete history other people have
already run.

```bash
python manage.py makemigrations --merge
```

This writes `0009_merge_...` with **no operations**. Its only job is to depend on
both `0008`s, so there is one newest file again.

**The catch:** `--merge` only works if the two changes are **independent**. Two
different fields, fine. Both changing the *same* field, or both renaming the same
table — the graph merges but the operations fight each other. You fix that by
hand.

### Q4. What is `django_migrations`? ✅ "deleting a row makes Django rerun it"

**The second half I missed:** it reruns against a database where **the SQL has
already happened**:

```
ProgrammingError: column "slug" of relation "tasks_project" already exists
```

> The files and the database each hold half the truth. This table is the link
> between them. **Django trusts the table, not the actual schema.**

That is why `--fake` exists:

```bash
python manage.py migrate tasks 0007 --fake   # change the row, run NO SQL
```

It means "trust me, the database is already in this state". The right tool when
the two halves have genuinely drifted apart. Also a great way to make things much
worse if you are wrong.

Same reason deleting an **applied** migration file is dangerous (I hit this in
2b): the row stays behind, pointing at a file that is gone.

### Q5. Rolling back in production ✅ mechanically right

> *I said:* "migrate back to the previous migration number." → `migrate tasks 0006`.

The question said **production**, which really means "and what goes wrong?"

1. **Not everything can be reversed.** A `RunPython` with no `reverse_code`
   simply refuses. That is why I wrote `RunPython.noop` in 2b. Same for `RunSQL`.
2. **Reversible does not mean nothing is lost.** Reversing `AddField` **drops the
   column**. The slug data is gone. Rolling forward again gives an empty column.
   Reversibility is about *structure* only.
3. **Rolling back is rarely what you actually want.** Code and schema are
   deployed separately, and down-migrations are almost never tested.

> **Roll forward, not back.** Write a new migration that fixes the problem.
> Only reverse when the migration is recent, isolated, and you have checked what
> data it destroys.

**The practice that means you never need to:** make each migration work with the
code that is **currently running**. Add columns before the code uses them. Stop
using a column before you drop it. This is called **expand/contract**. Then a
code rollback never needs a schema rollback — which is the scary situation.
