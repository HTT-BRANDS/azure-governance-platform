#!/bin/bash
# =============================================================================
# Container entrypoint — initialises DB, runs migrations, starts the app.
#
# Order matters:
#   1. init_db  — creates the base schema for SQLite (dev/test).
#                 For MSSQL/PostgreSQL this is a no-op; Alembic owns the DDL.
#   2. alembic upgrade head — apply incremental migrations (idempotent).
#                 Migration 001 is safe if the table was pre-created by
#                 create_all — it checks for existence before creating.
#   3. uvicorn  — serve the app.
# =============================================================================
set -euo pipefail

echo "=== Azure Governance Platform startup ==="
echo "Environment : ${ENVIRONMENT:-development}"
# Log DB host without password
DB_HOST=$(echo "${DATABASE_URL:-sqlite}" | sed 's|.*@||' | cut -d'/' -f1)
echo "DB host     : ${DB_HOST}"

# 1 — Create base schema tables (idempotent — skips tables that exist)
echo "--- Initialising base schema ---"
python - <<'PYEOF'
from app.core.database import init_db
init_db()
print("Base schema ready.")
PYEOF

# 2 — Run Alembic incremental migrations
echo "--- Running Alembic migrations ---"
python -m alembic upgrade head
echo "--- Migrations complete ---"

# 3 — Start the application
PORT="${PORT:-8000}"
echo "--- Starting uvicorn on port ${PORT} ---"
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --log-level "${LOG_LEVEL:-info}"
