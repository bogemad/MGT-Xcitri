#!/usr/bin/env bash
set -euo pipefail

if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
  source /opt/conda/etc/profile.d/conda.sh
  conda activate "${CONDA_ENV:-fq2allele}" || conda activate fq2allele
fi

export KRAKEN_DEFAULT_DB=${KRAKEN_DB:-/kraken-db}
/mlst/db/mlst-make_blast_db

cd /app
exec python Mgt/Mgt/MGT_processing/Reads2MGTAlleles/reads_to_alleles.py "$@"
