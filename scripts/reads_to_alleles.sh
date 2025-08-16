#!/usr/bin/env bash
set -euo pipefail

# Pass through the calling user's UID and GID so files created inside the container match host ownership
exec docker compose run --rm \
  -e UID="$(id -u)" \
  -e GID="$(id -g)" \
  --user "$(id -u):$(id -g)" \
  alleles "$@"