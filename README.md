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
docker compose up --build
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20+ recommended)  
- Docker Compose (v2 plugin or standalone)  

> **Tip**: On Linux you may need to add your user to `docker` group to run Docker without `sudo`.

---

## Configuration (.env)

Fill in MGT-Xcitri/.env (see example.env for comments). Manually set **POSTGRES_PASSWORD**, **DJANGO_EMAIL** and **DJANGO_SECRET_KEY**:

```
#Postgres settings  ### MUST add POSTGRES_PASSWORD
POSTGRES_USER=mgt
POSTGRES_PASSWORD=<<<enter-password-here>>>
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=xcitri

#Django Settings ### MUST add DJANGO_EMAIL and DJANGO_SECRET_KEY

DJANGO_SUPERUSER=Ref
DJANGO_EMAIL=<<<enter-email-here>>>
DJANGO_SECRET_KEY=<<<enter-random-secret-key-here>>>
DJANGO_SUPERUSER_PASSWORD=${POSTGRES_PASSWORD}
DB_INIT_FLAG=/var/lib/db_init/.db_initialized

# Email authentication settings
# Change "console" in the line below to "smtp" and complete and uncomment SMTP email settings below if you wish to use a real email acccount as your authentication server
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Your real SMTP details (if you wish to use real email authentication)
#EMAIL_HOST=
#EMAIL_PORT=
#EMAIL_HOST_USER=
#EMAIL_HOST_PASSWORD=
#EMAIL_USE_TLS=
#EMAIL_USE_SSL=
#EMAIL_TIMEOUT=

# Who should the emails appear to come from?
#DEFAULT_FROM_EMAIL=
#SERVER_EMAIL=

# Keep this if running server on current machine
MGT_URL="http://127.0.0.1:8000"

#Other settings - generally no change needed to these
DEBUG=False
MLST_WEBSITE_PASSWORD=${POSTGRES_PASSWORD}



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


