# SwachchhoHat (স্বচ্ছহাট)

Bangla-first agricultural market transparency platform. The current implementation is an early, connected development slice; see [PROJECT_STATUS.md](./PROJECT_STATUS.md) for what is and is not implemented.

## Run locally

Requirements: Python 3.11+, Node.js 20.19+ or 22.12+, and npm.

### Backend

In PowerShell:

```powershell
cd C:\Users\Oywon\Desktop\SwachhaHut\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.seed
uvicorn app.main:app --reload
```

The API and interactive OpenAPI docs are available at `http://localhost:8000` and `http://localhost:8000/docs`. SQLite is used by default for local development. Set `DATABASE_URL` to a PostgreSQL connection string for PostgreSQL; production schema changes need Alembic migrations before deployment.

Development mode creates an ephemeral signing key if `SECRET_KEY` is unset. Production must set `APP_ENV=production`, a `SECRET_KEY` of at least 32 characters, `DATABASE_URL`, and a restricted `CORS_ORIGINS` value.

### Frontend

In another PowerShell window:

```powershell
cd C:\Users\Oywon\Desktop\SwachhaHut
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000`. Set `VITE_API_BASE_URL` to the deployed API's `/api/v1` URL when deploying the frontend.

### Development-only accounts

Run the seed script to create accounts. All seeded accounts use password `DemoOnly!234`:

| Role | Phone |
| --- | --- |
| Farmer | +8801700000001 |
| Buyer | +8801700000002 |
| Moderator | +8801700000003 |
| Authority | +8801700000004 |
| Administrator | +8801700000005 |

These are public demo credentials and must never be reused in production. Phone/OTP verification is not implemented. Seeded Faridpur price inputs and observations are simulated, clearly marked data.

## Current API slice

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/users/me`
- `GET /api/v1/prices/fair-range`
- `POST /api/v1/transactions`, `GET /api/v1/transactions`, `POST /api/v1/transactions/{id}/confirm`
- `GET /api/v1/inventory/lots`, declaration and stock-movement endpoints
- `GET /api/v1/inventory/lots/{id}/history` verifies the lot's hash chain
- `GET /api/v1/notifications`

The fair-price calculation uses configured production-cost, margin, and range inputs. It is an explainable demonstration formula, not an economically validated forecast or an official price.

