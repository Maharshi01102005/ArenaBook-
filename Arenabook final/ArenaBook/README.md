# ArenaBook — Online Sports Venue Reservation System

A complete Django web application for discovering, comparing and booking sports
turfs and venues online, with a custom-built admin panel for managers.

Built to the Infolabz "Python-Django Final Project" specification (11 tables:
User, Country, State, City, UserProfile, SportCategory, Turf, TurfImage,
Booking, Payment, Review, ContactUs).

---

## 1. Quick start (5 commands)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py makemigrations arena
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open http://127.0.0.1:8000/

> Detailed PyCharm instructions are in **SETUP_PYCHARM.md**.

---

## 2. Login credentials (created by `seed_data`)

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@arenabook.com` | `Admin@123` |
| Customer | `rahul@example.com` | `User@123` |
| Customer | `priya@example.com` | `User@123` |
| Customer | `aman@example.com` / `sneha@…` / `karan@…` / `neha@…` | `User@123` |

Login is by **email address** (custom user model — there is no username field).

---

## 3. Where things live

| URL | What it is |
|-----|-----------|
| `/` | Public website (home, venues, booking, payments, reviews) |
| `/dashboard/` | Custom themed **admin panel** (staff only) |
| `/django-admin/` | Standard Django admin (superuser) |

---

## 4. Feature list

**Public website**
- Home page with hero search, featured venues, sport categories, stats, testimonials
- Sport-category browsing with per-category venue counts
- Venue listing with live filters: keyword, sport, city, price range, sorting, pagination
- Venue detail: image gallery, amenities, map-style address block, rating summary, reviews
- **Interactive slot picker** — pick a date, and the hourly grid loads by AJAX showing which
  slots are already taken (overlap-safe check against pending + confirmed bookings)
- Booking flow: select date + start/end time → price auto-calculated from `price_per_hour`
- Simulated payment gateway (Credit Card / Debit Card / PayPal / Other) with card formatting,
  transaction ID generation and automatic booking confirmation
- Printable invoice, booking history, booking cancellation
- Reviews with star ratings — only allowed for users with a **confirmed** booking at that venue,
  one review per user per venue, editable and deletable
- Registration, email login, profile page with avatar upload and chained
  Country → State → City dropdowns (AJAX)
- Contact Us form that stores messages for admins
- About page

**Admin panel (`/dashboard/`)**
- Dashboard with KPI cards (revenue, bookings, users, venues), Chart.js revenue trend,
  bookings-by-status doughnut, latest bookings and unread messages
- CRUD for Sport Categories, Venues (with multi-image gallery upload + featured/active toggles),
  Users (edit, activate/deactivate, staff flag), Locations (country/state/city)
- Booking management with status transitions (pending → confirmed → cancelled)
- Payment ledger with status control and revenue totals
- Review moderation
- Contact-message inbox with read/unread state
- Search, filters and pagination on every list screen

---

## 5. Design

Theme: **"floodlit pitch"** — deep pitch-green shell, chalk-white canvas, floodlight-amber
accent and clay highlights, with chalk-line circle/centre-line motifs used as a structural
device. Typography pairs *Space Grotesk* (display) with *Inter* (body). Bootstrap 5.3 is used
for layout only; all colour, elevation and component styling comes from
`static/css/style.css` design tokens. Fully responsive, dark sidebar admin shell.

---

## 6. Database

SQLite by default (`db.sqlite3`) so the project runs with zero configuration.

To switch to **MySQL**, open `arenabook/settings.py`, comment out the SQLite `DATABASES`
block, uncomment the MySQL block, fill in your credentials, then:

```bash
pip install mysqlclient
python manage.py migrate
python manage.py seed_data --fresh
```

---

## 7. Project structure

```
ArenaBook/
├── manage.py
├── requirements.txt
├── arenabook/                # project config
│   ├── settings.py  urls.py  wsgi.py  asgi.py
├── arena/                    # the single application
│   ├── models.py             # all 12 models
│   ├── forms.py              # auth, profile, booking, payment, review, admin forms
│   ├── views.py              # public site views
│   ├── dashboard_views.py    # admin panel views
│   ├── urls.py               # 49 named routes
│   ├── admin.py              # Django admin registrations
│   ├── signals.py            # auto-create UserProfile
│   ├── context_processors.py # global site context
│   ├── templatetags/arena_extras.py
│   └── management/commands/seed_data.py
├── templates/                # base, partials, pages, account, booking, dashboard
├── static/css/style.css  static/js/main.js
└── media/                    # uploaded images
```

---

## 8. Notes

- `Pillow` is required for the `ImageField`s — it is in `requirements.txt`.
- The `arena/migrations/` folder ships with only `__init__.py`; run
  `python manage.py makemigrations arena` once on first setup to generate `0001_initial.py`.
- The payment gateway is **simulated** (no real money moves). It always succeeds and is the
  right seam to plug Razorpay/Stripe into later.
- `DEBUG = True` for development. Set `DEBUG = False`, change `SECRET_KEY` and configure
  `ALLOWED_HOSTS` before any real deployment.
