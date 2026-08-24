# Chapter 3 — Python Syntax Crash Course (for a JS dev)

## Step 7 — Reading manage.py (= Python syntax crash course)

22 lines, and it contains most of the Python syntax I need.

### 1. Shebang
```python
#!/usr/bin/env python
```
"If executed directly, run me with python." Same as `#!/usr/bin/env node`.

### 2. Docstrings
```python
"""Django's command-line utility for administrative tasks."""
```
Looks like a comment, but it is a REAL string object attached to the
file/function — readable at runtime via `main.__doc__`.
JSDoc is a comment parsed from source; a docstring is data in memory.
Triple quotes = multi-line string (like a JS backtick template literal).

### 3. Imports
```python
import os                 # const os = require('os')
import sys                # const sys = require('sys')
from django.core.management import execute_from_command_line
#   ^ same as: const { execute_from_command_line } = require('django/core/management')
```
- `import X` -> the module name itself becomes the variable. No `const x =` part.
- `from X import Y` -> destructured import.
- `os` and `sys` are standard library. No install needed.

### 4. Functions, colons and INDENTATION
```python
def main():
    print("hi")          # indented = inside the function
```
```js
function main() {
  console.log("hi")
}
```
- `def` declares a function.
- The colon `:` OPENS a block. INDENTATION closes it. There are NO braces.
- **Indentation is syntax in Python, not formatting.** Wrong indentation =
  SyntaxError, not an ugly diff. Convention: 4 spaces.

### 5. Environment variables
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```
```js
process.env.DJANGO_SETTINGS_MODULE ??= 'config.settings'   // set only if unset
```
`os.environ` = `process.env`.

**This line is the link between `manage.py` and my `config/` folder.**
`"config.settings"` is a DOTTED import path = "the `settings` module inside the
`config` package" = `require('./config/settings')`. If I rename the `config`
folder, I must update this string.

### 6. try / except / raise
```python
try:
    from django.core.management import execute_from_command_line
except ImportError as exc:
    raise ImportError("Couldn't import Django...") from exc
```
| Python | JS |
|--------|-----|
| `try:` | `try {` |
| `except SomeError as e:` | `catch (e) {` |
| `raise` | `throw` |
| `raise X from exc` | `throw new Error(msg, { cause: e })` |

Difference: Python catches a SPECIFIC error TYPE, and I can stack several
`except` blocks for different failures. JS gives one untyped `catch` that I must
inspect myself.

(Fun fact: Django's own error message here says "Did you forget to activate a
virtual environment?" — the exact trap I hit in Step 3.)

### 7. sys.argv vs process.argv — DIFFERENT OFFSETS
```python
execute_from_command_line(sys.argv)
```
| | index 0 | index 1 | index 2 |
|---|---|---|---|
| Node `process.argv` | path to `node` | path to script | first real arg |
| Python `sys.argv` | path to script | first real arg | second real arg |

Python has no entry for the interpreter itself. Off-by-one trap when porting code.

### 8. `if __name__ == "__main__":`  <- THE IMPORTANT ONE
```python
if __name__ == "__main__":
    main()
```
```js
if (require.main === module) {
  main()
}
```
Every Python file has a `__name__` variable:
- run the file DIRECTLY -> `__name__` is the string `"__main__"`
- IMPORT the file from elsewhere -> `__name__` is the module's name

So this line means: "only run `main()` when this file is executed directly,
not when it is imported."

**Why it matters:** in Python, importing a module EXECUTES its top-level code.
Without this guard, importing `manage.py` would boot the whole Django command
machinery as a side effect. Exactly the same problem and the same fix as in Node.
