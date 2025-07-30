#!/usr/bin/env bash
set -euo pipefail

# Where we’ll write the dump on the host
OUTFILE=${1:-xcitri-$(date +%Y%m%dT%H%M%S).sql}

echo "🚀 Dumping database to ${OUTFILE}…"

# Run pg_dump inside the db container, streaming to the host file
docker compose exec -T db \
  pg_dump \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --no-owner \
  > "${OUTFILE}"

echo "✅ Dump complete: ${OUTFILE}"
