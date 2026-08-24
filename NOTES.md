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

## The Plan (roadmap)

| Phase | What we learn | Node/JS equivalent | Chapter |
|-------|---------------|--------------------|---------|
| 0 | Setup: virtualenv, pip, install Django | `node_modules`, `npm`, `npm install` | 1 (done) |
| 1 | Python crash course (only what backend needs) | JS syntax vs Python syntax | 3 (started) |
| 2 | Django project vs app, urls, views, runserver | Express app, routes, controllers | 2, 4 (done) |
| 3 | Models + ORM + migrations (the database) | Prisma / Sequelize models | -- |
| 4 | Django Admin (free CRUD dashboard) | nothing in Node gives you this free | -- |
| 5 | Django REST Framework: serializers, viewsets, routers | Zod/Joi validation + Express routers | -- |
| 6 | Authentication + permissions (JWT) | Passport / jsonwebtoken middleware | -- |
| 7 | Build the Task Manager API end to end | the real project | -- |
| 8 | Tests, env vars, deployment basics | Jest, dotenv, PM2/Docker | -- |

**Rules of this tutorial**
- One step at a time. Run the command, then understand what happened.
- Nothing is skipped as "magic" — if Django does something automatically,
  we open the file and look at it.

## Quick command reference

```bash
source venv/bin/activate            # ALWAYS first, in every new terminal tab
python manage.py runserver          # start dev server on :8000
python manage.py help               # list every available command
pip install X && pip freeze > requirements.txt   # install + lock, always together
which python                        # first debug step when Python misbehaves
find . -name '*.py' -not -path './venv/*'        # see only my own code
```
