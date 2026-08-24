# Chapter 2 — The Django Project Skeleton

## Step 5 — Generate the project skeleton

```bash
django-admin startproject config .
```

**Reading the command**
- `django-admin` -> CLI tool installed into `venv/bin/` along with Django.
  (Like `express-generator` / `nest new`.)
- `startproject` -> the subcommand: scaffold a new project.
- `config` -> name of the settings package to create.
- `.` -> "create it HERE". If I omit the dot, Django makes `config/config/`,
  a pointless nested folder. Always use the dot.

**Why the folder is named `config` and not `taskmanager`:** that folder holds
ONLY configuration — settings, root URL table, server entrypoints. My actual
features (tasks, users) will live in separate **apps** created later. Old
tutorials name it after the project, which tempts people into dumping feature
code there. `config` keeps the boundary obvious.

**What got created**

```
manage.py            <- entry point for every command I will ever run
config/
    __init__.py      <- marks the folder as an importable Python package
    settings.py      <- all configuration + middleware wiring
    urls.py          <- root route table
    wsgi.py          <- production entrypoint (sync servers)
    asgi.py          <- production entrypoint (async servers)
```

**Map to Express**

| Django | Express |
|--------|---------|
| `manage.py` | the `scripts` block in `package.json` |
| `config/settings.py` | config file + every `app.use(...)` middleware line |
| `config/urls.py` | root router: `app.use('/api', router)` |
| `config/wsgi.py` / `asgi.py` | `app.listen(3000)` |
| `config/__init__.py` | no equivalent — Python needs it to treat a folder as a package |

**TIP — don't run `ls -R`** in a Python project: it walks into `venv/` and
prints thousands of files. To see only my own code:

```bash
find . -name '*.py' -not -path './venv/*'
```

(Same trap as running `ls -R` on `node_modules` — I just never did that in Node.)

## Step 6 — Run the dev server

```bash
python manage.py runserver          # default port 8000 -> http://127.0.0.1:8000/
python manage.py runserver 3000     # custom port
# Ctrl+C to stop
```

Rocket ship page = success.

- The `18 unapplied migration(s)` warning is NORMAL at this stage. Django has
  built-in tables (users, sessions, permissions) not created yet. Fixed in Phase 3.
- The server auto-reloads on file save. That is `nodemon` behaviour, built in,
  no extra package.
- `manage.py` is the entry point for EVERY Django command:
  `python manage.py <command>`. Roughly what `npm run <script>` is in Node,
  except Django provides the commands instead of me writing them.

```bash
python manage.py help               # list every available command
```

Commands I will use most: `runserver`, `startapp`, `makemigrations`,
`migrate`, `createsuperuser`, `shell`, `test`.

