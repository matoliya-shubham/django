# Chapter 1 — Setup: virtualenv, pip, Django

## Step 1 — Create a virtual environment

```bash
cd ~/Documents/personal/django
/opt/homebrew/bin/python3.14 -m venv venv   # use the FULL path, see gotcha below
```

**What happened:** a new folder `venv/` appeared. Inside it there is a private
copy of Python (`venv/bin/python`) and a private `pip` (`venv/bin/pip`).
Any package we install from now on lands inside `venv/`, not on my whole machine.

**Reading the command:**
- `python3` -> run Python
- `-m venv` -> "run the built-in module named `venv`" (like `npx` running a bundled tool)
- `venv` -> the folder name to create (convention; could be any name, `.venv` is also common)

**JS comparison**

| Python | Node |
|--------|------|
| `python3 -m venv venv` | nothing needed — `node_modules` is automatic |
| `venv/` folder | `node_modules/` folder |
| never commit `venv/` to git | never commit `node_modules/` to git |

**Why Python needs this extra step:** `npm install` always installs into the
current project. Python's `pip install` installs *globally* by default, so two
projects wanting different Django versions would overwrite each other.
A virtual environment is how we force Python to behave like Node.

## Step 2 — Activate the virtual environment

```bash
source venv/bin/activate     # turn it ON  (prompt shows "(venv)")
which python                 # check: must end in django/venv/bin/python
deactivate                   # turn it OFF (only when I want to leave)
```

**What happened:** my prompt changed to `(venv) ...`. That means the shell now
finds `venv/bin/python` and `venv/bin/pip` before the system ones.

**How it works (no magic):** `source` runs a script that edits the `PATH`
environment variable of my current shell. `PATH` is the list of folders the
shell searches when I type a command. Activation just puts `venv/bin` at the
front of that list.

**IMPORTANT — things that trip people up**
- Activation lives in ONE terminal tab only. New tab / reboot / new window
  => run `source venv/bin/activate` again.
- If the prompt does not say `(venv)`, `pip install` will pollute my system
  Python instead of the project. Always glance at the prompt first.
- `source` is a shell builtin, nothing to do with Python.

**JS comparison:** Node needs no activation step — `npx jest` automatically
checks `./node_modules/.bin` first. Python makes that lookup manual and
per-terminal-session.

## GOTCHA — my Mac has more than one Python (this cost me Step 3 once)

**What went wrong:** I ran `python3 -m venv venv` twice. The first time
`python3` was Anaconda's Python 3.13, the second time it was Homebrew's
Python 3.14. The venv ended up half-and-half:

```
venv/bin/python  -> /opt/anaconda3/bin/python   (3.13, site-packages EMPTY)
venv/bin/pip     -> Homebrew 3.14               (installed django HERE)
```

So `pip install django` succeeded, but `python -m django --version` said
`No module named django` — because `python` and `pip` were looking in two
different folders.

**The fix (delete and rebuild with ONE explicit interpreter):**

```bash
deactivate
rm -rf venv                                   # safe: like rm -rf node_modules
/opt/homebrew/bin/python3.14 -m venv venv     # FULL path, no guessing
source venv/bin/activate
python --version                              # must say Python 3.14.2
```

**Why this can't happen in Node:** there is basically one `node` on my machine.
On macOS there are several Pythons — Apple's system one, Homebrew's, Anaconda's
— and bare `python3` means "whichever one wins the PATH race right now".
My Anaconda `base` env auto-activates in my shell (that's the `base` in my
prompt), which is why `python3` was Anaconda's.

**Rules I will follow from now on**
1. When creating a venv, always name the interpreter by full path.
2. When ANY Python command misbehaves, first command to run is `which python`.
3. Never create a venv twice into the same folder — delete it and start over.

**Debug commands worth remembering**

```bash
which python                        # which interpreter am I actually using?
python --version                    # which version?
ls -la venv/bin/python*             # what do the venv symlinks point to?
cat venv/pyvenv.cfg                 # which Python built this venv?
ls venv/lib/*/site-packages/        # what is actually installed, and under which version?
pip list                            # installed packages (like `npm ls --depth=0`)
```

## Step 3 — Install Django

```bash
pip install django
python -m django --version          # -> 6.1
```

**Result:** Django 6.1 installed. Three folders appeared in
`venv/lib/python3.14/site-packages/`:

| Package | What it is |
|---------|------------|
| `django` | the framework itself |
| `asgiref` | async plumbing Django uses under the hood |
| `sqlparse` | SQL formatter, used to pretty-print migrations |

Note that Django ships with almost no dependencies — 2 tiny ones. A fresh
Express app pulls dozens. Django's philosophy is "batteries included":
router, ORM, admin, auth, templates, and forms all live inside that one
`django` package instead of being separate npm-style libraries.

**pip vs npm cheat sheet**

| Task | Node | Python |
|------|------|--------|
| install a package | `npm install django` | `pip install django` |
| list installed | `npm ls --depth=0` | `pip list` |
| package manifest | `package.json` | `requirements.txt` (we create this manually) |
| freeze exact versions | `package-lock.json` (auto) | `pip freeze > requirements.txt` (manual) |
| install from manifest | `npm install` | `pip install -r requirements.txt` |
| where it lands | `node_modules/` | `venv/lib/python3.14/site-packages/` |
| uninstall | `npm uninstall django` | `pip uninstall django` |

Big difference: npm writes the lockfile for me automatically. In Python,
`requirements.txt` only updates when I run `pip freeze` myself.

## Step 4 — Lock dependencies into requirements.txt

```bash
pip freeze > requirements.txt
cat requirements.txt
```

Contents now:

```
asgiref==3.12.1
Django==6.1
sqlparse==0.6.0
```

**What it is:** the `dependencies` section of `package.json`, as a plain text
file. A teammate cloning this project runs:

```bash
pip install -r requirements.txt
```

**THE CATCH:** npm rewrites `package.json` + lockfile automatically on every
install. pip does NOT. Every time I `pip install` something new I must re-run
`pip freeze > requirements.txt` myself, or my environment silently drifts away
from my teammate's. This is a classic "works on my machine" bug source in
Python projects.

**Habit to build:** `pip install X` is always followed by
`pip freeze > requirements.txt`. Two commands, always together.

