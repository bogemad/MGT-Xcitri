#!/usr/bin/env bash
set -euo pipefail


exec docker compose run --rm \
  -e UID="$(id -u)" \
  -e GID="$(id -g)" \
  --user "$(id -u):$(id -g)" \
  alleles "$@"