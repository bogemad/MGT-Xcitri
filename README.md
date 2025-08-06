# MGT-Xcitri

Forked from [LanLab/MGT-local](https://github.com/LanLab/MGT-local)  
A Docker-powered, Django-based multilevel genome typing (MGT) database & web interface for _Xanthomonas citri_.

---

## Overview

This project bundles:

- A **Django** web application for browsing and querying MGT data  
- A **PostgreSQL** backend, automatically initialized on first run  
- A simple **email activation** workflow for user accounts  
- Scripts for **dumping/restoring** your local database  
- A pipeline for **calling alleles** from read/genome files

Everything runs via **Docker Compose**—no manual Python or Postgres installs required.

---

## Installation

```bash
# 1) Clone the repo
git clone https://github.com/bogemad/MGT-Xcitri.git
cd MGT-Xcitri

# 2) Copy & edit your env file
cp example.env .env

# 3) Build & start the stack
docker compose up -d --build
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20+ recommended)  
- Docker Compose (v2 plugin or standalone)  

> **Tip**: On Linux you may need to add your user to `docker` group to run Docker without `sudo`.

---

## Configuration (.env)

Fill in MGT-Xcitri/.env (see example.env for comments). At minimum set your passwords and Django SECRET_KEY:

```
##########################
# PostgreSQL (backend)
##########################
POSTGRES_DB=xcitri
POSTGRES_USER=mgt
POSTGRES_PASSWORD=<choose-a-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432

##########################
# Django settings
##########################
SECRET_KEY=<choose-a-secret-key>
DEBUG=False
DB_INIT_FLAG=/var/lib/db_init/.db_initialized

##########################
# Initial user & DB setup
##########################
MLST_WEBSITE_PASSWORD=<choose-a-password>
DJANGO_SUPERUSER_PASSWORD=<choose-a-password>

##########################
# Email (for activation & reset)
##########################
# Use console printing in local deployment:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# For real SMTP:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.example.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=you@example.com
# EMAIL_HOST_PASSWORD=<app-password>
# EMAIL_USE_TLS=True
# DEFAULT_FROM_EMAIL=you@example.com
# SERVER_EMAIL=you@example.com

MGT_URL="http://127.0.0.1:8000"
```

## Running the Server

After `docker compose up`:

- **First run only**: the init script will create the DB schema, superuser, and MLST role.  
- **Subsequent runs** skip DB init and go straight to Django.

Open your browser at:

```
http://127.0.0.1:8000/
```
or change to the ip address of your remote machine if running remotely (also change MGT_URL in .env)

---

## Testing Email

- **Console backend** writes activation emails to your web logs:

  ```bash
  docker compose logs -f web
  ```

- **SMTP** will send real mail—trigger a password reset at `/accounts/password_reset/`.

---

## Typing Isolates (Pipeline)

> **Under development**—the cron pipeline is not fully wired up.  

1. **Generate alleles** from reads/genomes:  
   ```bash
   # on host or inside the web container
   conda activate mgtenv
   cd Mgt/Mgt/MGT_processing/Reads2MGTAlleles
   ./README.md  # follow that README to run reads_to_alleles.py
   ```

2. **Upload** the resulting allele files + metadata via the web UI (create a Project).

3. **(Future)** Run the cron pipeline to finalize allele calls & MGT assignment:

   ```bash
   cd Mgt/Mgt/Scripts
   python cron_pipeline.py \
     -s Mgt.settings_template \
     -d xcitri \
     --allele_to_db \
     --local
   ```

---

## Dump & Restore Database

We provide helper scripts under `scripts/` so **no Docker knowledge** is needed.

### Dump (export)

```bash
# writes xcitri-<timestamp>.sql in the repo root

./dump_db.sh [optional-output-filename.sql]
```

### Load (import)

```bash
# restores from a local file or remote URL
./load_db.sh path-or-URL-to-dump.sql
```

> These scripts use your running `db` service and the credentials in `.env.db`.

---

## 🚧 Pushing to Remote

To push a dump to a staging/production Postgres (outside Docker):

```bash
./push_db.sh \
  path-to-local-dump.sql \
  postgres://user:pass@staging.example.org:5432/xcitri
```

---

## 📄 License

GPLv3.0 License — see [LICENSE](LICENSE) for details.  
Feel free to reuse, adapt, and redistribute for academic and non-commercial use.  


