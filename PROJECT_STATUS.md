# Project status

Updated: 2026-11-20

## Implemented and locally testable

- React + TypeScript + Vite public landing page and market-price view.
- Registration/login for farmer and buyer roles; Argon2 password hashes and signed bearer tokens.
- FastAPI + SQLAlchemy API with SQLite development default and PostgreSQL driver support.
- Explicitly simulated Faridpur onion price seed, surfaced as demo data in the UI.
- Configured, Decimal-based price-range calculation with methodology and input/source metadata.
- Farmer sale submission, buyer-only confirmation/dispute, and verified lot creation only after confirmation.
- Buyer inventory declarations and nonnegative partial stock release/loss movements.
- Entity-scoped SHA-256 chained audit events for transaction and inventory actions, with verification endpoint.
- Role checks and owner checks for the implemented transaction and inventory APIs.
- Focused backend workflow tests.

## Not implemented yet — do not represent as production-ready

- Alembic migrations, PostgreSQL deployment verification, concurrency controls for critical inventory/audit writes, and production secrets/session strategy.
- OTP/phone verification, refresh/revocation, password recovery, uploads, rate limiting, and comprehensive security hardening.
- 48-hour transaction expiry worker/notifications beyond lazy expiry when a farmer or buyer lists transactions.
- Full location/crop administration, authoritative price-source integrations, validated forecasting, and price history endpoints.
- Radar indicators/modeling, moderator cases, authority reports, appeals, and administrative workflows.
- Document ingestion, pgvector, multilingual embeddings, hybrid retrieval, reranking, sourced RAG answers, and RAG evaluation.
- Public aggregation/privacy thresholds, maps, SMS provider integration, offline/USSD integration, CSV/PDF reports, CI/CD, Docker, and deployment configuration.
- Full test coverage, frontend tests, accessibility/responsive browser verification, and production operations documentation.

## Suggested next steps

1. Add Alembic and PostgreSQL-backed integration tests; make transaction confirmation and inventory changes safe under concurrent requests.
2. Implement account verification and secure production session/refresh-token handling.
3. Add transaction/dispute evidence and moderator review/appeal workflows.
4. Add configured price data management, historic observations, and a tested baseline forecast.
5. Add explainable Radar rules and human review before any authority escalation.
6. Add actual document ingestion/retrieval behind configured embedding/LLM providers; do not fabricate citations.
7. Complete public aggregation safeguards, roles, deployment, CI, frontend tests, and operational documentation.

