# ACP App Boilerplate

Minimal full-stack starter for the Advanced Computer Programming class, Department of Robotics and AI Engineering, KMITL.

## Stack

- Next.js Pages Router
- React
- shadcn-style UI components with Tailwind CSS
- Native `fetch()` for API calls
- FastAPI
- PostgreSQL
- Docker Compose

## Run

```bash
git clone https://github.com/syanyong/acpapp.git
cd acpapp
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- FastAPI: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`

## Pages

- `/` — static landing page with example user cards
- `/login` — login form using the FastAPI auth API

## API

### GET `/health`

Checks that the backend can reach the database. Returns `503` if the database is unavailable.

### POST `/api/auth/register`

Creates a customer or business account and sets an HTTP-only session cookie.

### POST `/api/auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Example User",
  "role": "customer"
}
```

Response:

```json
{
  "id": "...",
  "email": "user@example.com",
  "full_name": "Example User",
  "role": "customer",
  "subscription_tier": null
}
```

The frontend sends credentials with requests so the HTTP-only session cookie is used for `/api/auth/me` and other protected endpoints.

## Database

The backend creates these tables from the SQLAlchemy models in `backend-api/database.py`:

```sql
users (...)
businesses (...)
```

The `password` column stores a bcrypt hash, not plaintext.

## Project structure

```text
.
├── docker-compose.yaml
├── backend-api/
│   ├── app.py
│   ├── database.py
│   ├── deps.py
│   ├── routes/
│   │   └── auth.py
│   ├── schemas.py
│   └── security.py
│   └── requirements.txt
└── nextjs/
    ├── components/ui/
    ├── lib/utils.js
    ├── pages/
    │   ├── _app.js
    │   ├── index.js
    │   └── login.js
    ├── styles/globals.css
    ├── components.json
    ├── tailwind.config.js
    └── package.json
```

This repository is intentionally small. Students can add CRUD, authorization, state management, and additional tables later as course exercises.
