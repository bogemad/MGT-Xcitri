#!/usr/bin/env bash
set -Eeuo pipefail

#############################################
# MGT-Xcitri install / re-install script
# - Checks .env and required vars customised
# - Detects prior install and (optionally) nukes it
# - Builds & starts services fresh
#
# Usage:
#   ./scripts/install.sh [--force] [--nuke] [--no-up]
#############################################

PROJECT_NAME_DEFAULT="mgt-xcitri"
COMPOSE_FILE_DEFAULT="compose.yaml"
# Common ports for this stack (adjust if your compose uses different)
PORTS_TO_CHECK=("5432" "8000")

# CLI flags
FORCE=0
NUKE=0
NO_UP=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --nuke)  NUKE=1 ;;
    --no-up) NO_UP=1 ;;
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
  else
    ok "No matching volumes detected."
  fi

  local nets
  nets=$(docker network ls --format '{{.Name}}' | grep -E "^${pname}(_default|$)" || true)
  if [[ -n "$nets" ]]; then
    warn "Detected networks:
$nets"
  else
    ok "No matching networks detected."
  fi
}

nuke_stack() {
  local pname="$1"
  warn "This will stop & remove containers, images, volumes, and orphan resources for project '$pname'."
  confirm "Proceed with full clean-up (IRREVERSIBLE)?" || die "Aborted."

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

build_and_up() {
  local pname="$1"
  info "Building images…"
  docker compose -p "$pname" build

  if [[ $NO_UP -eq 1 ]]; then
    ok "Build complete. Skipping 'up' as requested (--no-up)."
    return
  fi

  info "Running initial setup and starting stack…"
  docker compose -p "$pname" up -d

  #add while loop test for complete setup?

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

  report_existing_stack "$pname"

  if [[ $NUKE -eq 1 ]]; then
    nuke_stack "$pname"
  else
    warn "Existing resources (if any) were NOT removed. Use --nuke to fully reset."
  fi

  build_and_up "$pname"
}

main "$@"
