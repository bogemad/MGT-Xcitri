#!/usr/bin/env bash
set -Eeuo pipefail

#############################################
# MGT-Xcitri install / re-install script
# - Checks .env and required vars customised
# - Detects prior install and (optionally) nukes it
# - Builds & starts services fresh
#
# Usage:
#   ./scripts/install.sh [--force] [--nuke]
#############################################

PROJECT_NAME_DEFAULT="mgt-xcitri"
COMPOSE_FILE_DEFAULT="compose.yaml"
# Common ports for this stack (adjust if your compose uses different)
PORTS_TO_CHECK=("5432" "8000")
# First-run init wait config
INIT_FLAG_PATH="/var/lib/db_init/.db_initialized"  # inside web container
INIT_CHECK_INTERVAL=5   # seconds between checks
INIT_TIMEOUT=900        # 15 min max wait (adjust as needed)
LOG_DIR="./logs"
LOG_FILE="${LOG_DIR}/install.log"
# CLI flags
FORCE=0
NUKE=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --nuke)  NUKE=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

# Pretty helpers
info()  { printf "\033[1;34m[INFO]\033[0m %s\n"  "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m %s\n"  "$*"; }
error() { printf "\033[1;31m[ERR ]\033[0m %s\n"  "$*" >&2; }
ok()    { printf "\033[1;32m[ OK ]\033[0m %s\n"  "$*"; }

die() { error "$*"; exit 1; }

confirm() {
  if [[ $FORCE -eq 1 ]]; then return 0; fi
  read -r -p "${1:-Are you sure?} [y/N] " ans
  case "$ans" in
    [yY][eE][sS]|[yY]) return 0 ;;
    *) return 1 ;;
  esac
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command '$1'. Please install it and retry."
}

project_root_check() {
  [[ -f "$COMPOSE_FILE_DEFAULT" ]] || die "No $COMPOSE_FILE_DEFAULT found here. Run this from the MGT-Xcitri repo root."
  ok "Compose file found: $COMPOSE_FILE_DEFAULT"
}

load_env_if_present() {
  if [[ -f ".env" ]]; then
    set -a
    . ./.env
    set +a
    ok ".env loaded"
  else
    die "No .env file found. Create one (you can start from .env.example) and re-run."
  fi
}

read_var_from_file() {
  # read_var_from_file FILE KEY -> value (no quotes)
  local file="$1" key="$2"
  local line val
  line=$(grep -E "^\s*${key}\s*=" "$file" 2>/dev/null | tail -n1 || true)
  [[ -z "$line" ]] && return 1
  val="${line#*=}"
  val="${val## }"; val="${val%% }"
  # strip quotes if any
  val="${val%\"}"; val="${val#\"}"
  val="${val%\'}"; val="${val#\'}"
  printf "%s" "$val"
}

validate_env_vars() {
  local missing=()
  for key in DJANGO_SUPERUSER POSTGRES_PASSWORD DJANGO_EMAIL DJANGO_SECRET_KEY; do
    if [[ -z "${!key:-}" ]]; then
      missing+=("$key")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    die "The following required variables are missing in .env: ${missing[*]}"
  fi

  # Compare to .env.example if present to ensure values were actually changed
  if [[ -f ".env.example" ]]; then
    for key in DJANGO_SUPERUSER POSTGRES_PASSWORD DJANGO_EMAIL DJANGO_SECRET_KEY; do
      local default_val actual_val
      default_val="$(read_var_from_file ".env.example" "$key" || true)"
      actual_val="${!key}"
      if [[ -n "$default_val" && "$default_val" == "$actual_val" ]]; then
        die "Your $key in .env still matches the example default. Please change it to a secure/project-specific value."
      fi
    done
  else
    warn "No .env.example to compare against; applying heuristic checks."
  fi

  # Heuristic checks
  [[ ${#POSTGRES_PASSWORD} -ge 8 ]] || die "POSTGRES_PASSWORD should be at least 12 characters."
  [[ "$DJANGO_EMAIL" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]] || die "DJANGO_EMAIL doesn’t look like a valid email."
  [[ ${#DJANGO_SECRET_KEY} -ge 24 ]] || die "DJANGO_SECRET_KEY should be at least 24 characters (prefer 32+)."

  ok "Environment variables look good."
}

report_existing_stack() {
  local pname="$1"
  info "Checking for existing Docker resources for project: $pname"

  docker compose -p "$pname" ps || true
  docker compose -p "$pname" images || true

  local vols
  vols=$(docker volume ls --format '{{.Name}}' | grep -E "^${pname}(_|$)" || true)
  if [[ -n "$vols" ]]; then
    warn "Detected volumes:
$vols"
    is_vols=1
  else
    ok "No matching volumes detected."
    is_vols=0
  fi

  local nets
  nets=$(docker network ls --format '{{.Name}}' | grep -E "^${pname}(_default|$)" || true)
  if [[ -n "$nets" ]]; then
    warn "Detected networks:
$nets"
    is_nets=1
  else
    ok "No matching networks detected."
    is_nets=0
  fi
let is_exist=is_vols+is_nets
if [[ is_exist == 0 ]]; then
  return 1
else
  return 0
fi
}

nuke_stack() {
  local pname="$1"
  info "Bringing down stack and removing images/volumes/orphans…"
  docker compose -p "$pname" down --rmi all --volumes --remove-orphans || true

  info "Removing leftover volumes matching ${pname}_* (if any)…"
  docker volume ls --format '{{.Name}}' | grep -E "^${pname}(_|$)" | xargs -r docker volume rm || true

  info "Removing dangling images and builder cache…"
  docker image prune -f || true
  docker builder prune -f || true

  info "Attempting network clean-up…"
  docker network ls --format '{{.Name}}' | grep -E "^${pname}(_default|$)" | xargs -r docker network rm || true

  ok "Clean slate for '$pname'."
}

wait_for_first_run_init() {
  local pname="$1"
  local started_at elapsed cid health

  mkdir -p "$LOG_DIR"

  info "Streaming logs while waiting for first-run initialisation…"
  started_at=$(date +%s)

  # stream logs to console AND save to file
  docker compose -p "$pname" logs -f --no-color 2>&1 | tee "$LOG_FILE" &
  local log_pid=$!

  # ensure we clean up log streaming on function exit
  trap "kill $log_pid 2>/dev/null || true" RETURN

  while :; do
    elapsed=$(( $(date +%s) - started_at ))
    if (( elapsed >= INIT_TIMEOUT )); then
      error "Timed out after ${INIT_TIMEOUT}s waiting for initialisation flag."
      die "Initialisation did not complete in time. Logs are in $LOG_FILE"
    fi

    cid="$(docker compose -p "$pname" ps -q web || true)"
    if [[ -z "$cid" ]]; then
      sleep "$INIT_CHECK_INTERVAL"
      continue
    fi

    health="$(docker inspect --format='{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "unknown")"
    if [[ "$health" == "unhealthy" ]]; then
      error "Web container is unhealthy."
      die "Container reported unhealthy state. Logs are in $LOG_FILE"
    fi

    if docker exec "$cid" bash -lc "[[ -f '$INIT_FLAG_PATH' ]]"; then
      ok "Initialisation flag found inside web container."
      return 0
    fi

    sleep "$INIT_CHECK_INTERVAL"
  done
}

build_and_up() {
  local pname="$1"
  info "Building images…"
  
  docker compose -p "$pname" build
  docker compose run --rm kraken-init

  info "Running initial setup and starting stack…"
  docker compose -p "$pname" up -d

  wait_for_first_run_init "$pname"

  ok "Stack is up. Use 'docker compose -p \"$pname\" ps' to view status."
}

main() {
  require_cmd docker
  require_cmd grep
  require_cmd awk
  if ! docker compose version >/dev/null 2>&1; then
    die "'docker compose' (v2) is required. Please install/upgrade Docker Desktop or docker-compose-plugin."
  fi

  project_root_check

  local pname
  pname="mgt-xcitri"
  info "Using compose project name: $pname"

  load_env_if_present
  validate_env_vars
  
  if report_existing_stack "$pname"; then
    warn "Previous installation detected. Would you like to perform a clean install?
    This will stop & remove containers, images, volumes, and orphan resources for project '$pname'.

    IMPORTANTLY: This will also delete any existing MGT database. If you have uploaded and called alleles on existing isolates and wish to keep this data, please dump your database to file prior to running this script.

    A clean install should only be done if there have been problems with a previous install or wish to start again. Clean installs should be done with a freshly cloned git repository (previous MGT-Xcitri dirctory removed and git clone https://github.com/bogemad/MGT-Xcitri.git)
    "
    if confirm "Proceed with clean install (IRREVERSIBLE)? Press N to exit."; then
      nuke_stack "$pname"
    else
      exit
    fi
  fi
  build_and_up "$pname"
}

main "$@"
