# Chapter 9 — The Django Admin

A full CRUD dashboard over my models, generated at runtime from the model
definitions. No scaffolding step, no generated files to maintain.

**JS:** there is no equivalent. Closest is bolting on AdminJS or Retool and
wiring every resource by hand. Here it's already installed —
`django.contrib.admin` was in `INSTALLED_APPS` from `startproject`, and
`config/urls.py` has routed `admin/` since day one.

## Getting in

```bash
python manage.py createsuperuser
```

The admin is behind `django.contrib.auth`, so it needs a user row with
`is_staff` and `is_superuser`. Then `/admin/` — but it only lists models I've
**registered**.

## Registering — two styles

`tasks/admin.py` is the whole config surface. It's imported automatically at
startup because `tasks` is in `INSTALLED_APPS` — I never import it myself.

```python
admin.site.register(Project)              # bare: default everything

@admin.register(Task)                     # decorator: attach a config class
class TaskAdmin(admin.ModelAdmin):
    ...
```

Both do the same thing. `Project` gets the defaults; `Task` gets a
`ModelAdmin` — a **description of the UI**, not a view. Django reads the
attributes and builds the pages.

## The four options I set

| Option | Effect |
|---|---|
| `list_display` | which **columns** the list page shows |
| `list_filter` | the filter sidebar on the right |
| `search_fields` | the search box, `icontains` across the listed fields |
| `list_select_related` | performance — see below |

`list_display` accepts field names **or method names** on the model or the
`ModelAdmin`, so computed columns are free.

`list_filter` only makes sense on low-cardinality fields — `status` has three
values, `project` a handful. Putting `title` there would render thousands of
sidebar links.

## `__str__` is the admin's label

Every dropdown, every FK column, the breadcrumb after saving — all of it calls
`__str__()`. Without the ones on `Project` and `Task` the whole UI reads
`Project object (1)`.

That method was written back in Chapter 5 for the shell. The admin quietly
reuses it. Worth remembering: `__str__` is not debug output, it's the
user-facing name of the row.

## The N+1, seen for real

Chapter 8 taught `select_related` in the shell. The admin is where it bites
without being asked.

Putting `project` in `list_display` means each row renders
`task.project.name` — a separate query per row. 100 tasks = **101 queries**,
and nothing in the UI hints at it.

```python
list_select_related = ("project",)
```

Same JOIN as `select_related`, declared instead of called — I don't own the
queryset here, the `ModelAdmin` does. Deleting the line brings the N+1 straight
back.

> Any FK in `list_display` needs a matching entry in `list_select_related`.

## Gotchas

- unregistered model = invisible in the admin, no error, no warning
- `list_filter` / `search_fields` are **tuples** — a lone `("status")` is a
  string, not a tuple; it needs the trailing comma
- the admin is staff-facing, not a public API — it's for me and whoever runs
  the app, never the customer
- `search_fields` with no index does a full table scan on every keystroke
