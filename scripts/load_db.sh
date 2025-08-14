#!/usr/bin/env bash
set -euo pipefail

# First arg: path or URL of a .sql dump
SRC=${1:?Please provide a local filename or HTTP URL for the dump}

echo "⚙️  Preparing to load database from ${SRC}…"

# If it's a URL, stream via curl; otherwise read from file
if [[ "${SRC}" =~ ^https?:// ]]; then
  echo "🔗 Downloading and restoring from URL…"  
  curl -fsSL "${SRC}" | \
    docker compose exec -T db psql \
      --username="${POSTGRES_USER}" \
      --dbname="${POSTGRES_DB}"
else
  echo "📂 Restoring from local file…"  
  docker compose exec -T db psql \
      --username="${POSTGRES_USER}" \
      --dbname="${POSTGRES_DB}" \
    < "${SRC}"
fi

echo "✅ Database restored from ${SRC}"
