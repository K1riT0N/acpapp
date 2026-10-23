# Nadd นัด: bookings for local shops

Course project for Advanced Computer Programming (Department of Robotics and AI Engineering, KMITL).

Nadd is a booking website for small businesses such as hair salons, massage shops and car care. Customers find a
shop, pick a service, day and time, and pay a deposit to confirm. The shop gets an alert for each new booking, and
both sides get reminders before the appointment. Deposits aren't refunded if the customer cancels or doesn't show
up; the rest is paid at the shop. Shops on the Free plan get 10 bookings a month; Pro costs ฿299 a month and has no
limit.

Payments (PromptPay) run in **test mode**, and LINE and email messages are **shown in the app's Messages page**
instead of being sent. Both have one clear place to plug in the real service later (see
[Going live](#going-live-real-payments-and-messages)).

## Run it

You need Docker Desktop.

```bash
git clone https://github.com/K1riT0N/acpapp.git
cd acpapp
cp .env.example .env          # then change the passwords and JWT_SECRET in .env
docker compose up -d --build
docker compose exec backend-api python seed.py
```

| What | Where |
|---|---|
| Website | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs (try every endpoint) | http://localhost:8000/docs |
| System check (website → API → database) | http://localhost:3000/status |

### Demo accounts

Every demo account uses the password **demo1234**. The login page has one-click buttons for them.

| Account | Role |
|---|---|
| ploy@demo.nadd | Customer (LINE) |
| ton@demo.nadd | Customer (email) |
| noi@demo.nadd | Owner of Baan Suay Hair Studio (Free) |
| mek@demo.nadd | Owner of Clean Ride Car Care (Pro) |
| somjai@demo.nadd | Owner of Somjai Thai Massage (Free) |

The demo data (`backend-api/nadd_seed_data.json`) is written as if today were 23 Sep 2026. `seed.py` moves every
date forward to today, so there are always bookings in today's queue and reminders still to come.

- `python seed.py` adds the demo rows that are missing (safe to run twice).
- `python seed.py --reset` **deletes all data** and loads the demo again with today's dates. Use it before a demo,
  or if the API won't start because of tables from an older version.

### Run the tests

```bash
docker compose exec backend-api python -m pytest
```

The tests create and use a separate database (`nadd_test`), so your data isn't touched. They cover the booking
rules: slots, full slots, the monthly limit, holds that run out, double booking with simultaneous requests,
deposit maths, the messages and their wording, cancel, complete, no-show, and Free/Pro plans.

### Useful commands

```bash
docker compose logs -f backend-api     # see the API, the background jobs and the simulated LINE/email sends
docker compose restart backend-api     # after changing .env
docker compose down                    # stop (data is kept)
docker compose down -v                 # stop and delete the database
```

## What each kind of user can do

**Visitors** search shops by name, service or area, filter by category and see each shop's services, prices and
opening hours.

**Customers** pick a service, one of the next 14 days and a free time, then have 15 minutes to pay the deposit. They
see their tickets under My bookings, can cancel a confirmed booking before it starts (the deposit is kept), and get
confirmations and reminders in Messages.

**Shop owners** see a dashboard with today's queue, the next 7 days against an estimate of their capacity, this
month's usage and the latest alerts. On the day they mark each booking completed (choosing cash, PromptPay or card
for the rest of the price) or a no-show. They manage services, shop details, the deposit rate and opening hours, and
can upgrade to Pro or switch back to Free.

## How it works

```text
Browser ── Next.js (port 3000) ──fetch + JWT──► FastAPI (port 8000) ──SQLAlchemy──► PostgreSQL 16
                                                     │
                                                     └── APScheduler, every 30 s: expire unpaid holds,
                                                         send due reminders, end finished Pro months
```

- **Front-end** (`nextjs/`): Next.js pages router in JavaScript. The design is the prototype's CSS, copied into
  `styles/globals.css` with the same class names. Pages fetch JSON from the API through `lib/api.js`.
- **Login**: passwords are stored as bcrypt hashes. Logging in returns a JWT (user id and role, valid 7 days,
  signed with `JWT_SECRET`) that the browser keeps in `localStorage` and sends as `Authorization: Bearer ...`. The
  API checks the role on every protected route; what the pages show is only for convenience.
- **Back-end** (`backend-api/`): routes in `routes/` only check input and call the business rules in `core/`, which
  are plain Python functions that the tests call directly.
- **Database**: 9 tables (`models.py`) with string IDs, money in whole baht and CHECK constraints for every
  allowed value, created at start-up with `Base.metadata.create_all`.

### Business rules

| Rule | Where |
|---|---|
| A slot starts every 30 minutes and must end by closing time; it's full when overlapping bookings reach "customers at once" | `core/slots.py` |
| A new booking is held for 15 minutes. An unpaid hold stops counting the moment it runs out, even before the job marks it expired | `core/status.py` |
| Free plan: 10 bookings a month (read from the `plans` table). Expired holds don't count | `core/limits.py` |
| No double booking: the slot and limit checks and the insert run in one transaction that locks the shop row (`SELECT ... FOR UPDATE`) | `core/bookings.py` |
| Deposit = price × deposit % / 100, rounded half up; price, deposit and remainder are copied onto the booking | `core/bookings.py` |
| The customer must accept the no-refund policy before paying; the time is saved in `policy_accepted_at` | `core/payments.py` |
| Messages go by LINE if the person has a LINE ID, otherwise email; reminders 24 h (both) and 2 h (customer) before | `core/notify.py` |
| Every shop always has one current subscription; Pro lasts one month and then falls back to Free | `core/plans.py` |
| "Now" and "today" are always Bangkok time | `core/timeutil.py` |

## Going live: real payments and messages

- **Payments**: all payment code is in `backend-api/core/payments.py`. Replace `pay_deposit_test()` with a payment
  gateway in test mode (for example Omise or Stripe PromptPay), add a webhook route that verifies the gateway's
  signature, and call `confirm_deposit()` from it. Never trust the browser to say it paid.
- **LINE and email**: `send_line()` and `send_email()` in `backend-api/core/notify.py` only log today. Fill them in
  with the LINE Messaging API (push message; LINE Notify was shut down in 2025) and an email service. Nothing else
  needs to change.

## API

All endpoints return JSON. Errors are `{"detail": "a sentence the user can read"}`. The full, clickable list is at
http://localhost:8000/docs.

| Who | Endpoints |
|---|---|
| Anyone | `GET /health`, `GET /plans`, `GET /shops?q=&category=`, `GET /shops/{id}`, `GET /shops/{id}/calendar`, `GET /shops/{id}/slots`, `GET /shops/sample-slot` |
| Accounts | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /auth/demo-accounts` |
| Customer | `POST /bookings`, `GET /bookings/me`, `GET /bookings/{id}`, `POST /bookings/{id}/pay-deposit`, `/release`, `/cancel` |
| Shop owner | `GET /owner/dashboard`, `GET /owner/bookings?filter=`, `POST /owner/bookings/{id}/complete`, `/no-show`, `GET/POST /owner/services`, `PATCH /owner/services/{id}`, `GET/PATCH /owner/shop`, `PUT /owner/shop/hours`, `GET /owner/plan`, `POST /owner/plan/upgrade`, `/downgrade` |
| Logged in | `GET /notifications/me`, `POST /notifications/read-all`, `POST /notifications/send-now` |

## Project structure

```text
.
├── docker-compose.yaml         db, backend-api (8000), nextjs (3000)
├── .env.example                copy to .env
├── backend-api/
│   ├── app.py                  FastAPI app, CORS, routers, starts the scheduler
│   ├── database.py             engine, sessions
│   ├── models.py               the 9 tables
│   ├── schemas.py              JSON shapes in and out
│   ├── security.py             bcrypt, JWT, role checks
│   ├── scheduler.py            background jobs
│   ├── seed.py                 loads nadd_seed_data.json
│   ├── core/                   business rules (bookings, slots, limits, payments, notify, plans, ...)
│   ├── routes/                 auth, shops, plans, bookings, owner, notifications
│   └── tests/                  pytest
└── nextjs/
    ├── pages/                  one file per page (/, /shops/[id], /book/..., /pay/..., /owner/..., ...)
    ├── components/             Header, Footer, Ticket, BookingTable, FakeQR, Meter, OwnerActions, Toasts, ...
    ├── lib/                    api.js (fetch + token), auth.js, messages.js, format.js
    └── styles/globals.css      the prototype's design
```

## Troubleshooting

- **The API won't start and the log says a column "does not exist"**: the database still has tables from an older
  version. Run `docker compose run --rm backend-api python seed.py --reset`, then `docker compose up -d`.
- **Port 5432 is already in use**: PostgreSQL is already running on your computer. Change `"5432:5432"` to
  `"5433:5432"` in `docker-compose.yaml`.
- **The website says it can't reach the server**: check http://localhost:8000/health and
  `docker compose logs backend-api`.
