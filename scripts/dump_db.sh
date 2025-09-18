#!/usr/bin/env bash
set -euo pipefail

set -a; source $(dirname $0)/../.env; set +a

# Where we’ll write the dump on the host
OUTFILE=${1:-xcitri-$(date +%Y%m%dT%H%M%S).sql}

echo "🚀 Dumping xcitri database to ${OUTFILE}…"

# Run pg_dump inside the db container, streaming to the host file
docker compose exec -T db \
  pg_dump \
    --username="${POSTGRES_USER}" \
    --dbname="xcitri" \
    --no-owner \
  > "${OUTFILE}"

echo "✅ Xcitri dump complete: ${OUTFILE}"

OUTFILE=${1:-xcitrimal-$(date +%Y%m%dT%H%M%S).sql}
echo "🚀 Dumping xcitrimal database to ${OUTFILE}…"
# Run pg_dump inside the db container, streaming to the host file
docker compose exec -T db \
  pg_dump \
    --username="${POSTGRES_USER}" \
    --dbname="xcitrimal" \
    --no-owner \
  > "${OUTFILE}"

echo "✅ Xcitrimal dump complete: ${OUTFILE}"
