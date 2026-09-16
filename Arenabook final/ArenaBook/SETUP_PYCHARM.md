# Running ArenaBook in PyCharm — step by step

## Step 1 — Open the project
Unzip `ArenaBook.zip`, then in PyCharm choose **File → Open…** and select the
`ArenaBook` folder (the one containing `manage.py`). Open it in a new window.

## Step 2 — Create the interpreter (virtual environment)
**File → Settings → Project: ArenaBook → Python Interpreter → Add Interpreter →
Add Local Interpreter → Virtualenv Environment → New**
- Base interpreter: Python 3.10 or newer
- Location: leave as `ArenaBook/.venv`
- Click **OK** and wait for PyCharm to finish creating it.

## Step 3 — Install the packages
Open the PyCharm terminal (**Alt+F12**) — the venv activates automatically — and run:

```bash
pip install -r requirements.txt
```

This installs Django 5.x and Pillow (needed for image uploads).

## Step 4 — Create the database
Still in the terminal:

```bash
python manage.py makemigrations arena
python manage.py migrate
```

You should see a long list of `Applying …  OK` lines and `db.sqlite3` appear in the
project tree.

## Step 5 — Load the demo data
```bash
python manage.py seed_data
```

This creates the admin account, 6 customers, 4 states, 11 cities, 8 sport categories,
14 venues, ~40 bookings with payments, reviews and contact messages. The login
credentials are printed at the end.

Use `python manage.py seed_data --fresh` to wipe and regenerate the demo data.

## Step 6 — Run the server
Either run in the terminal:

```bash
python manage.py runserver
```

…or set up a PyCharm run configuration (nicer, gives you the green ▶ button):

**Run → Edit Configurations… → + → Django Server**
- Name: `ArenaBook`
- Host: `127.0.0.1`, Port: `8000`
- Python interpreter: the `.venv` you created
- Working directory: the project root

> If the *Django Server* template is missing (PyCharm Community Edition), add a plain
> **Python** configuration instead: Script path = `manage.py`, Parameters = `runserver`.

Then press ▶.

## Step 7 — Open it
| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | The website |
| http://127.0.0.1:8000/dashboard/ | The custom admin panel |
| http://127.0.0.1:8000/django-admin/ | Django's built-in admin |

Sign in with **admin@arenabook.com / Admin@123** to reach the admin panel, or
**rahul@example.com / User@123** to browse as a customer.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'django'`**
The terminal is not using the venv. Close and reopen the PyCharm terminal, or run
`.venv\Scripts\activate` (Windows) / `source .venv/bin/activate` (macOS/Linux).

**`Cannot use ImageField because Pillow is not installed`**
Run `pip install Pillow`.

**`no such table: arena_user`**
Migrations were not applied — run Step 4 again.

**Images don't show after upload**
Make sure `DEBUG = True` in `arenabook/settings.py` during development; media files are
served by `arenabook/urls.py` only in debug mode.

**Port 8000 already in use**
`python manage.py runserver 8001`

**Want to start over completely**
Delete `db.sqlite3` and `arena/migrations/0001_initial.py`, then repeat Steps 4 and 5.
