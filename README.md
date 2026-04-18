# herokuapp

A refreshed version of an older Heroku-era Python app.

## What it does

- login-protected comic/image viewer
- URL parsing for supported comic sources
- simple math answer viewer from PostgreSQL
- IP echo endpoint

## Modernisation included

- migrated from `web.py` to **Flask**
- Python **3.11** target
- **uv** project management via `pyproject.toml`
- **Docker** support
- environment-variable configuration
- compatibility fallback for legacy `db.conf.ini`
- refreshed templates/CSS/JS structure

## Run locally with uv

```bash
uv sync
uv run flask --app app.main run --debug
```

Open <http://127.0.0.1:5000>

## Run with Docker

```bash
docker build -t herokuapp .
docker run --rm -p 8000:8000 \
  -e SECRET_KEY=change-me \
  herokuapp
```

Open <http://127.0.0.1:8000>

## Configuration

Set values via environment variables when possible:

- `SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `PASSWORD_SALT`
- `SESSION_DIR`
- `LOG_LEVEL`

Legacy fallback:
- `db.conf.ini` is still supported for database settings and password salt.

## Notes

- `/ip` remains public.
- `/math` and the main viewer require login.
- Password validation still supports the legacy SHA1+salt format for compatibility; this should be upgraded separately if you still use local auth.
