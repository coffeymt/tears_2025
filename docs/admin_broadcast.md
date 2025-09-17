# Admin Broadcast: configuration and usage

This document explains how to configure SMTP credentials for the admin broadcast feature and how to run broadcasts safely in development and production.

## Environment variables
The application reads SMTP/email configuration from environment variables (configured via `app/core/config.py`). Add the following to your `.env` or secret store:

- `SMTP_HOST` — SMTP server host (e.g., `mail.smtp2go.com`)
- `SMTP_PORT` — SMTP server port (e.g., `587`)
- `SMTP_USER` — SMTP username
- `SMTP_PASSWORD` — SMTP password (sensitive: store in secret manager or local `.env`, do NOT commit)
- `SMTP_USE_TLS` — `true` or `false` (recommended `true` for SMTPS/TLS)
- `MAIL_FROM` — The From header to use for broadcasts, e.g. `"SBCC Tears <michael@sbcctears.com>"`
- `BROADCAST_REPLY_TO` — Optional Reply-To address for broadcast responses

Example (local `.env` - do not commit):

```
SMTP_HOST=mail.smtp2go.com
SMTP_PORT=587
SMTP_USER=mcoffey_sbcc
SMTP_PASSWORD=your_smtp_password_here
SMTP_USE_TLS=true
MAIL_FROM="SBCC Tears <michael@sbcctears.com>"
BROADCAST_REPLY_TO=coffey.mikey@gmail.com
```

## How the app sends broadcast emails

- The admin broadcast endpoint (`POST /api/admin/broadcast`) calls the service in `app/services/admin.py` to build a recipient list based on a filter (`all`, `active`, `unpaid`).
- The primitive email sender is `app/utils/email.py` exposing `send_email(to, subject, body)` which the code (and tests) use. Tests monkeypatch this function — keep its signature stable when changing it.

## Running a broadcast (development)

1. Ensure your `.env` contains `SMTP_PASSWORD` (or set the env var in your shell). Example in PowerShell:

```powershell
$env:SMTP_HOST = 'mail.smtp2go.com';
$env:SMTP_PORT = '587';
$env:SMTP_USER = 'mcoffey_sbcc';
$env:SMTP_PASSWORD = '...';
$env:SMTP_USE_TLS = 'true';
$env:MAIL_FROM = '"SBCC Tears <michael@sbcctears.com>"';
$env:BROADCAST_REPLY_TO = 'coffey.mikey@gmail.com'
```

2. From the project root run the dev server (or use TestClient for dry runs):

```powershell
# run server
poetry run start
# or
uvicorn app.main:app --reload
```

3. Call the broadcast endpoint with an admin token. Example `curl`:

```powershell
curl -X POST "http://localhost:8000/api/admin/broadcast" -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" -d '{"subject":"Test","body":"Hello","filter":"active"}'
```

## Safety recommendations

- For large recipient lists, prefer queueing (e.g., a background worker with RQ/Celery) instead of sending synchronously in the web request. This prevents request timeouts and allows retries for transient SMTP failures.
- Deduplicate recipient emails before sending to avoid duplicates.
- Respect SMTP provider rate limits; consider batching with a pause between batches.
- In production, store SMTP credentials in a secret manager (Azure Key Vault, AWS Secrets Manager, etc.) and never commit them to source control.

## Tests

- Unit tests for the broadcast feature mock `app.utils.email.send_email` to avoid sending real email. See `tests/test_admin_broadcast.py`.
- To run the broadcast tests only:

```powershell
pytest tests/test_admin_broadcast.py -q
```

## Next steps / optionally useful improvements

- Move sending into a background worker with retry handling for transient failures.
- Add per-recipient status reporting (success/failure) and expose partial results in the API response.
- Support an alternate provider HTTP API (SMTP2GO HTTP API) for better reporting and rate-limiting features.

---

Document created on 2025-09-17
