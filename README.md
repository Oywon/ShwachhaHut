# SwachchhoHat (স্বচ্ছহাট)

### A Bangla-First Agricultural Market Transparency Platform

SwachchhoHat is an agricultural market transparency platform designed to improve fair-price awareness, transaction accountability, and stock visibility in Bangladesh's agricultural supply chain.

The platform aims to help farmers make informed selling decisions while making agricultural transactions more transparent through buyer-confirmed records, inventory tracking, and auditable stock histories.

> **Project Status:** Early-stage development. The current implementation represents a connected development slice rather than the complete proposed platform. Refer to [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) for a detailed overview of implemented features, limitations, and pending development work.

---

## Table of Contents

- [Key Objectives](#key-objectives)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Vercel Multi-Service Deployment](#vercel-multi-service-deployment)
- [Development Accounts](#development-accounts)
- [Available API Endpoints](#available-api-endpoints)
- [Current Implementation Notes](#current-implementation-notes)
- [Environment Configuration](#environment-configuration)
- [Security Considerations](#security-considerations)

---

## Key Objectives

SwachchhoHat is being developed around the following objectives:

- **Fair-Price Awareness:** Provide an explainable agricultural fair-price range based on configured production costs, margins, and market observations.
- **Transaction Transparency:** Maintain transaction records that require confirmation from both farmers and buyers.
- **Inventory Visibility:** Track declared stock, storage information, and stock movements.
- **Tamper-Evident Records:** Maintain verifiable transaction histories using a hash-linked audit mechanism.
- **Market Accountability:** Support future monitoring and review of unusual inventory and market activity.
- **Accessibility:** Build a Bangla-first experience suitable for farmers and other agricultural market participants.

The initial development scope focuses on onion markets in Faridpur, Bangladesh.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | SQLite (local development), PostgreSQL (deployment) |
| API Documentation | OpenAPI / Swagger UI |
| Package Management | npm, pip |
| Development Environment | Windows PowerShell |

---

## Getting Started

Follow these instructions to run SwachchhoHat locally.

### Prerequisites

Ensure the following tools are installed:

- Python 3.11+
- Node.js 20.19+ or 22.12+
- npm
- Git (recommended)

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SwachchhaHut
```

Replace `<YOUR_REPOSITORY_URL>` with the actual repository URL.

### 2. Backend Setup

Open PowerShell and navigate to the backend directory:

```powershell
cd C:\Users\Oywon\Desktop\SwachhaHut\backend
```

Create and activate a Python virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the required dependencies:

```powershell
pip install -r requirements.txt
```

Create the environment configuration file:

```powershell
Copy-Item .env.example .env
```

Initialize the development database and seed the demo data:

```powershell
python -m app.seed
```

Start the FastAPI development server:

```powershell
uvicorn app.main:app --reload
```

The backend will be available at:

- **API Base:** http://localhost:8000
- **Interactive API Documentation:** http://localhost:8000/api/docs
- **Alternative API Documentation:** http://localhost:8000/api/redoc

### 3. Frontend Setup

Open a separate PowerShell window and navigate to the project root:

```powershell
cd C:\Users\Oywon\Desktop\SwachhaHut
```

Install the frontend dependencies:

```powershell
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

Open the local URL displayed in your terminal (typically `http://localhost:5173`).

The Vite development server is configured to proxy `/api` requests to the backend running at `http://localhost:8000`.

## Vercel multi-service deployment

The root `vercel.json` defines two services: `app` (Vite at `/`) and `backend` (FastAPI routed publicly under `/api/*`). The API already mounts its routes at `/api/v1`, and the frontend uses the same-origin `/api/v1` path. Browser requests enter through Vercel's public rewrite; neither service makes a server-side call to the other, so no service binding is needed.

Before deploying, configure these Vercel project environment variables for **Production** (and Preview if desired):

- `APP_ENV=production`
- `DATABASE_URL` set to a persistent managed PostgreSQL URL. SQLite is rejected in production because Vercel function storage is ephemeral.
- `SECRET_KEY` set to a unique random value of at least 32 characters. Do not commit it or share it in chat.
- `CORS_ORIGINS` set to the frontend origin(s) only if cross-origin browser access is needed; same-origin `/api` routing does not require CORS.

The backend accepts `postgres://` and `postgresql://` provider URLs and routes them through the installed Psycopg 3 SQLAlchemy driver.

The Vercel project `oywons-projects/swachchhohat` is linked to this local checkout. Production deployment is pending a persistent `DATABASE_URL`; the local Vercel build has not completed on Windows because the CLI could not create package symlinks. No production deployment has been verified.

---

## Development Accounts

The database seed script creates the following development-only accounts.

All seeded accounts use the same password:

```text
DemoOnly!234
```

| Role | Phone Number |
|---|---|
| Farmer | +8801700000001 |
| Buyer | +8801700000002 |
| Moderator | +8801700000003 |
| Authority | +8801700000004 |
| Administrator | +8801700000005 |

**Important:** These credentials are intended exclusively for local development and demonstration. Never use them in a production environment.

Phone number and OTP verification are not currently implemented.

The seeded Faridpur price inputs and market observations are simulated data. They are explicitly intended for development and demonstration, not as verified market information.

---

## Available API Endpoints

The current backend provides the following API functionality under `/api/v1`.

### Authentication and User Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate a user |
| GET | `/users/me` | Retrieve the authenticated user's profile |

### Fair-Price Information

| Method | Endpoint | Description |
|---|---|---|
| GET | `/prices/fair-range` | Retrieve the configured fair-price range |

### Transactions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/transactions` | Create a transaction |
| GET | `/transactions` | Retrieve transaction records |
| POST | `/transactions/{id}/confirm` | Confirm a transaction |

### Inventory Management

| Method | Endpoint | Description |
|---|---|---|
| GET | `/inventory/lots` | Retrieve inventory lots |
| POST | Inventory declaration endpoint | Submit an inventory declaration |
| POST | Stock movement endpoint | Record a stock movement |
| GET | `/inventory/lots/{id}/history` | Retrieve and verify an inventory lot's audit history |

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications` | Retrieve notifications for the authenticated user |

For complete request parameters, response schemas, and interactive testing, visit the Swagger documentation at:

http://localhost:8000/docs

---

## Current Implementation Notes

### Database Configuration

SQLite is used by default for local development.

To use PostgreSQL, configure the `DATABASE_URL` variable in your backend `.env` file with a valid PostgreSQL connection string.

Production database schema changes must be managed through Alembic migrations before deployment.

### Fair-Price Calculation

The current fair-price calculation uses configurable inputs, including:

- Production cost
- Reasonable profit margin
- Configured price-range inputs

The calculation is designed to be explainable. However, it is currently a demonstration formula and should not be interpreted as an economically validated forecasting model or an official agricultural market price.

### Transaction Confirmation

The current transaction workflow supports transaction creation and buyer confirmation.

### Inventory Audit History

Inventory lot histories use a hash-linked audit mechanism. The history endpoint checks the integrity of the recorded hash chain.

This provides tamper-evident records; it should not be interpreted as an absolute guarantee against privileged database modification or system compromise.

### Simulated Data

Seeded Faridpur price inputs and market observations are simulated.

The application must distinguish simulated information from verified market observations and user-submitted transactions.

---

## Environment Configuration

The backend uses a `.env` file for environment-specific configuration.

Start with the provided template:

```powershell
Copy-Item .env.example .env
```

Important configuration variables include:

| Variable | Purpose |
|---|---|
| `APP_ENV` | Application environment |
| `SECRET_KEY` | Application signing key |
| `DATABASE_URL` | Database connection string |
| `CORS_ORIGINS` | Allowed frontend origins |

### Production Requirements

Before deploying the backend, configure:

- `APP_ENV=production`
- A strong `SECRET_KEY` containing at least 32 characters
- A valid production `DATABASE_URL`
- A restricted `CORS_ORIGINS` value containing only trusted frontend origins

In development mode, the application generates an ephemeral signing key when `SECRET_KEY` is not configured. Production deployments must explicitly provide a persistent secret key.

Never commit `.env` files or production secrets to GitHub.

For Vercel's same-origin frontend/API routing, `VITE_API_BASE_URL` can be left unset. If explicitly configured, use:

```env
VITE_API_BASE_URL=/api/v1
```

Do not set a Vercel service binding URL in this frontend variable; the browser reaches the backend through the public `/api/*` rewrite.

---

## Security Considerations

- Development credentials must never be reused in production.
- Production deployments must use a persistent, secure signing key.
- CORS should allow only trusted frontend origins.
- Database schema changes should be applied through migrations.
- User-submitted information should be validated before processing.
- Simulated data must never be presented as verified market information.
- Transaction and inventory records should retain their audit history.

---

## Project Vision

SwachchhoHat aims to make agricultural markets more transparent, accessible, and accountable.

By combining fair-price awareness, verified transaction records, inventory visibility, and data-driven market monitoring, the platform seeks to strengthen farmers' bargaining power and support a more transparent agricultural supply chain in Bangladesh.

**SwachchhoHat — Building a Fairer and More Transparent Agricultural Market.**
