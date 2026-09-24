# Django Notes — Index

> My revision notes. One chapter per topic, in `notes/`.
> Every step is written in plain language with a JavaScript comparison
> wherever Python does things differently.

## Chapters

| # | Chapter | Covers |
|---|---------|--------|
| 1 | [Setup: virtualenv, pip, Django](notes/01-setup-venv-and-pip.md) | venv, activate, pip, requirements.txt, the two-Pythons gotcha |
| 2 | [The Django Project Skeleton](notes/02-django-project-skeleton.md) | `startproject`, what each generated file does, `runserver` |
| 3 | [Python Syntax Crash Course](notes/03-python-syntax-crash-course.md) | imports, `def`, indentation, try/except, `__name__ == "__main__"`, `sys.argv` |
| 4 | [Apps, Views and URLs](notes/04-apps-views-and-urls.md) | project vs app, `startapp`, views, `urlpatterns`, `include()`, first endpoint |
| 5 | [Models and Migrations](notes/05-models-and-migrations.md) | `models.Model`, field types, `null` vs `blank`, `makemigrations`, reading the migration file, `sqlmigrate` |
| 6 | [Postgres in Docker and DBeaver](notes/06-postgres-in-docker-and-dbeaver.md) | `docker-compose.yml`, named volumes, `.env` + `python-dotenv`, psycopg 3, DBeaver, `migrate`, `django_migrations` |
| 7 | [The ORM](notes/07-the-orm.md) | `manage.py shell`, create/filter/get/update/delete, `__` lookups, lazy QuerySets, `Q`/`F`, cheatsheet |
| 8 | [Relations](notes/08-relations.md) | `ForeignKey`, `project_id`, `related_name`, spanning `__`, N+1 and `select_related`, `on_delete` |
| 9 | [The Django Admin](notes/09-django-admin.md) | `createsuperuser`, registering models, `ModelAdmin`, `list_display`/`list_filter`/`search_fields`, `__str__`, `list_select_related` |

## The Plan

The roadmap, progress checkboxes, assignments and interview drills live in
**[CURRICULUM.md](CURRICULUM.md)** — one source of truth, read it at the start
of every session. This file is just the notes index.

**Rules of this tutorial**
- One step at a time. Run the command, then understand what happened.
- Nothing is skipped as "magic" — if Django does something automatically,
  we open the file and look at it.

## Quick command reference

```bash
docker compose up -d                # start Postgres, FIRST thing each day
source venv/bin/activate            # ALWAYS next, in every new terminal tab
python manage.py runserver          # start dev server on :8000
python manage.py help               # list every available command
pip install X && pip freeze > requirements.txt   # install + lock, always together
which python                        # first debug step when Python misbehaves
find . -name '*.py' -not -path './venv/*'        # see only my own code
```

## Database quick reference

```bash
docker compose up -d                # start Postgres in the background
docker compose ps                   # up? healthy? which host port?
docker compose logs -f db           # tail Postgres logs
docker compose down                 # remove container, KEEP data (named volume)
docker compose down -v              # remove container AND DESTROY data
docker compose exec db psql -U django -d django_tasks   # psql shell inside the container

python manage.py makemigrations tasks   # write the migration file (no DB access)
python manage.py sqlmigrate tasks 0001  # preview the SQL it will run
python manage.py showmigrations         # [X] applied / [ ] pending
python manage.py migrate                # apply to the database
```

Postgres runs on host port **5433**, not 5432 — a Homebrew `postgresql@15`
already owns 5432 on this machine. See Chapter 6.
