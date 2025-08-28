# MGT-Xcitri

Forked from [LanLab/MGT-local](https://github.com/LanLab/MGT-local)  
A Docker-based multilevel genome typing (MGT) database & web interface for _Xanthomonas citri_.

---

## Installation

```bash
# 1) Clone the repo
git clone https://github.com/bogemad/MGT-Xcitri.git
cd MGT-Xcitri

# 2) Copy & edit your env file
cp example.env .env

# 3) Build the kraken database
docker compose run --rm kraken-init

# 4) Build & start the stack
docker compose up

#OR run in detached mode (no console output)
docker compose up -d
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20+ recommended)  
- Docker Compose (v2 plugin or standalone)  

> **Tip**: On Linux you may need to add your user to `docker` group to run Docker without `sudo`.

---

## Configuration (.env)

Fill in MGT-Xcitri/.env (see example.env for comments). Manually set **POSTGRES_PASSWORD**, **DJANGO_SUPERUSER**, **DJANGO_EMAIL** and **DJANGO_SECRET_KEY**:

```
#Postgres settings  ### MUST add POSTGRES_PASSWORD
POSTGRES_USER=mgt
POSTGRES_PASSWORD=<enter-password-here>
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=xcitri

#Django Settings ### MUST add DJANGO_SUPERUSER, DJANGO_EMAIL and DJANGO_SECRET_KEY

DJANGO_SUPERUSER=<enter-superusername ##MUST not be "Ref">
DJANGO_EMAIL=<enter-email-here>
DJANGO_SECRET_KEY=<enter-secret-key-here>
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

#Kraken settings set KRAKEN_DB_PATH if you have an existing local kraken database you wish to use, otherwise KRAKEN_URL will be downloaded and used.
KRAKEN_DB_PATH=
KRAKEN_URL=https://ccb.jhu.edu/software/kraken/dl/minikraken_20171019_8GB.tgz
```

## Running the Server

After `docker compose up`:

- **First run only**: the init script will create the DB and build the website based on the X. citri scheme.  
- **Subsequent runs** will skip the DB init.

Open your browser at:

```
http://127.0.0.1:8000/
```
or change to the ip address of your remote machine if running remotely (also change MGT_URL in .env)

---

## Email configuration

- Users can create accounts within the MGT website, where a **Console backend** writes activation emails to your web logs or to the console if not running in detached mode (docker compose up):
  Use the link produced on the console or find it in the log with:
  ```bash
  docker compose logs -f web
  ```

- Users can also use real email activation by uncommenting and completing **SMTP** settings in `./.env`.

---

## Typing Isolates

> To type isolates, first extract alleles and other information from genome assemblies or raw reads using `./scripts/reads_to_alleles.py`

> Alleles can also be processed as a batch by completing `./allele_file_details.tsv` and running `./scripts/extract_alleles.py`

1. **Extract** alleles and other information from genome assemblies or raw reads using `./scripts/reads_to_alleles.py`

   OR

   Alleles can also be extracted as a batch by completing `./allele_file_details.tsv` and running `./scripts/extract_alleles.py`

2. **Upload** the resulting allele files + metadata via the web UI (create a Project).

3. **Finalise** allele calls & assign MGT by running:

   `./scripts/call_alleles.sh`

---

## Dump & Restore Database

Helper scripts are available to export (dump) and import databases from the docker image and allow mobility of the database. 

**Note** that all user details (usernames, passwords, etc.) will also be exported with the database dump.

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

> These scripts use your running `db` service and the credentials in `.env`. The website must be "up" to run these successfully.

---

## 📄 License

GPLv3.0 License — see [LICENSE](LICENSE) for details.  
Feel free to reuse, adapt, and redistribute for academic and non-commercial use.  


