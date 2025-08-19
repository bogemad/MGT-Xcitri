#!/usr/bin/env python3
"""
extract_alleles.py

Batch driver for running Reads2MGTAlleles through the Docker wrapper
(./scripts/reads_to_alleles.py) with auto-mount detection.

It reads ./data/allele_file_details (TSV with: strainid <tab> files) and
runs the pipeline for each sample. Input files are expected to exist
on the host filesystem; the wrapper will detect and mount their parent
directories automatically.

Outputs are written into ./data/alleles inside the repo, and finally
moved into --out_dir for manual upload.

Example:
  ./scripts/extract_alleles.py \
      --source_dir /path/to/my/files \
      --out_dir /path/to/upload_later \
      --species_key Xcitri
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import ast
from pathlib import Path

REPO_BASE = Path(__file__).resolve().parents[1]
DETAILS_FILE = REPO_BASE / "data" / "allele_file_details"
WRAPPER = REPO_BASE / "scripts" / "reads_to_alleles.py"
SETTINGS = REPO_BASE / "Mgt" / "Mgt" / "Mgt" / "settings_template.py"
REF_ALLELES = REPO_BASE / "species_specific_alleles" / "Xcitri_intact_alleles.fasta"
ALLELES_DIR = REPO_BASE / "data" / "alleles"
PATHOVAR_KEY = REPO_BASE / "mlst" / "mlst_pathovar_key.txt"

FASTQ = {".fastq", ".fq"}
FASTA = {".fasta", ".fa", ".fna"}

def strip_gz(p: Path) -> Path:
    return Path(p.stem) if p.suffix.lower() == ".gz" else p

def infer_intype(paths):
    exts = {strip_gz(Path(p)).suffix.lower() for p in paths}
    if len(paths) == 2:
        return "reads"
    if len(paths) == 1:
        if exts & FASTA:
            return "genome"
        if exts & FASTQ:
            return "reads"
    return "reads" if len(paths) == 2 else "genome"

def parse_species_cutoffs(settings_path: Path, species_key: str) -> dict:
    txt = settings_path.read_text(encoding="utf-8")
    m = re.search(r"SPECIES_SEROVAR\s*=\s*(\{.*?\})\s*\n", txt, re.DOTALL)
    if not m:
        raise RuntimeError(f"Could not locate SPECIES_SEROVAR in {settings_path}")
    spec = ast.literal_eval(m.group(1))
    if species_key not in spec:
        raise KeyError(f"Species key '{species_key}' not found; available: {list(spec.keys())}")
    return spec[species_key]

def read_details(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if not row or len(row) < 2:
                continue
            sid = row[0].strip()
            files = [x.strip() for x in row[1].split(",") if x.strip()]
            if sid and files:
                yield sid, files

def ensure_paths():
    ALLELES_DIR.mkdir(parents=True, exist_ok=True)

def run_wrapper(strainid, intype, input_paths, o_arg, cutoffs,
                threads, memory, kraken_db, force, pathovar_key, dry_run):
    i_arg = ",".join(str(p) for p in input_paths)
    cmd = [
        str(WRAPPER),
        "-i", i_arg,
        "--intype", intype,
        "--refalleles", str(REF_ALLELES),
        "-o", o_arg + "/",
        "--strainid", strainid,
        "--species", cutoffs.get("species", "Xanthomonas citri"),
        "--threads", str(threads),
        "--memory", str(memory),
        "--min_largest_contig", str(cutoffs["min_largest_contig"]),
        "--max_contig_no", str(cutoffs["max_contig_no"]),
        "--genome_min", str(cutoffs["genome_min"]),
        "--genome_max", str(cutoffs["genome_max"]),
        "--n50_min", str(cutoffs["n50_min"]),
        "--hspident", str(cutoffs["hspident"]),
        "--locusnlimit", str(cutoffs["locusnlimit"]),
        "--snpwindow", str(cutoffs["snpwindow"]),
        "--densitylim", str(cutoffs["densitylim"]),
        "--refsize", str(cutoffs["refsize"]),
        "--blastident", str(cutoffs["blastident"]),
    ]
    if kraken_db:
        cmd += ["--kraken_db", kraken_db]
    if pathovar_key:
        cmd += ["--pathovar", pathovar_key]
    if force:
        cmd += ["--force"]

    print("[RUN]", " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.run(cmd, cwd=REPO_BASE).returncode

def main():
    ap = argparse.ArgumentParser(
        description="Batch executor for Reads2MGTAlleles",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--details_file", type=Path, default=DETAILS_FILE)
    ap.add_argument("--source_dir", type=Path, required=True,
                    help="Directory containing the files referenced in details_file")
    ap.add_argument("--out_dir", type=Path, required=True,
                    help="Output directory for allele files")
    ap.add_argument("--settings_file", type=Path, default=SETTINGS)
    ap.add_argument("--species_key", default="Xcitri")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--memory", type=int, default=8)
    ap.add_argument("--kraken_db", default=None)
    ap.add_argument("--pathovar_key", default=PATHOVAR_KEY, help=f"Text file translating MLST result to phylogenetic-associated pathovar. Default {PATHOVAR_KEY}")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    ensure_paths()
    cutoffs = parse_species_cutoffs(args.settings_file, args.species_key)

    failures = 0
    for strainid, file_list in read_details(args.details_file):
        print(f"\n=== Sample: {strainid} ===")
        try:
            src_files = []
            for f in file_list:
                p = Path(f)
                if not p.is_absolute():
                    p = args.source_dir / f
                if not p.exists():
                    raise FileNotFoundError(f"Input not found: {p}")
                src_files.append(p.resolve())

            intype = infer_intype(src_files)
            if intype == "reads" and len(src_files) != 2:
                raise ValueError(f"Reads input requires 2 files, got {len(src_files)}")

            rc = run_wrapper(strainid, intype, src_files, args.out_dir, cutoffs,
                             args.threads, args.memory, args.kraken_db,
                             args.force, args.pathovar_key, args.dry_run)
            if rc != 0:
                raise RuntimeError(f"reads_to_alleles failed (exit {rc})")

        except Exception as e:
            failures += 1
            print(f"[ERROR] {strainid}: {e}")

    if failures:
        print(f"\nDone with {failures} failure(s).")
    else:
        print("\nDone. All samples processed successfully.")

if __name__ == "__main__":
    main()
