#!/usr/bin/env python3
import argparse
import ast
import os
import re
import shlex
import subprocess
import sys
from typing import Dict, Tuple, Optional

# -------- helpers to load SPECIES_SEROVAR safely (no importing settings) --------
def extract_species_serovar(settings_path: str) -> Dict:
    """
    Read /settings/settings_template.py and literal-eval the SPECIES_SEROVAR dict
    without executing the rest of the settings file (which requires env vars).
    """
    if not os.path.isfile(settings_path):
        raise FileNotFoundError(f"settings file not found: {settings_path}")
    text = open(settings_path, "r", encoding="utf-8").read()

    # Find 'SPECIES_SEROVAR = {' ... balanced braces ... '}'
    m = re.search(r"SPECIES_SEROVAR\s*=\s*\{", text)
    if not m:
        raise ValueError("Could not find SPECIES_SEROVAR assignment in settings file.")
    start = m.end() - 1  # index of '{'
    brace = 0
    end = None
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            brace += 1
        elif c == "}":
            brace -= 1
            if brace == 0:
                end = i + 1
                break
    if end is None:
        raise ValueError("Could not parse SPECIES_SEROVAR dict (unbalanced braces).")
    dict_str = text[start:end]
    try:
        return ast.literal_eval(dict_str)
    except Exception as e:
        raise ValueError(f"Failed to parse SPECIES_SEROVAR as a Python literal: {e}")

def pick_species_block(species_map: Dict, key: str) -> Dict:
    if key not in species_map:
        raise KeyError(
            f"Species key '{key}' not found in SPECIES_SEROVAR. "
            f"Available: {', '.join(sorted(species_map.keys()))}"
        )
    return species_map[key]

# -------- input discovery / command building --------
def resolve_input_paths(name_or_list: str,
                        reads_dir: str,
                        assemblies_dir: str) -> Tuple[str, str]:
    """
    Given column 2 value (either single file or 'r1,r2'), decide whether the files
    live in reads_dir or assemblies_dir and return (intype, input_arg_value).
    - If comma present => paired reads; look under reads_dir.
    - Else: try assemblies first (genome), else reads (single-end).
    """
    val = name_or_list.strip()
    if "," in val:
        # paired reads
        parts = [p.strip() for p in val.split(",") if p.strip()]
        cand = [os.path.join(reads_dir, p) for p in parts]
        if not all(os.path.isfile(p) for p in cand):
            raise FileNotFoundError(f"Paired reads not found under {reads_dir}: {', '.join(cand)}")
        return "reads", ",".join(cand)

    # single file: prefer assemblies; else reads
    a_path = os.path.join(assemblies_dir, val)
    r_path = os.path.join(reads_dir, val)
    if os.path.isfile(a_path):
        return "genome", a_path
    if os.path.isfile(r_path):
        return "reads", r_path
    raise FileNotFoundError(f"Input '{val}' not found in {assemblies_dir} or {reads_dir}")

def build_command(python_exe: str,
                  reads_to_alleles: str,
                  strainid: str,
                  intype: str,
                  input_value: str,
                  threads: int,
                  species_params: Dict,
                  outpath: str,
                  refalleles: str,
                  extra: Optional[Dict[str, str]] = None) -> list:
    """
    Build the subprocess command list for reads_to_alleles.py with all required flags.
    """
    # Mandatory args
    cmd = [
        python_exe, reads_to_alleles,
        "-i", input_value,
        "--intype", intype,
        "--refalleles", refalleles,
        "--strainid", strainid,
        "-o", outpath,
        "--threads", str(threads),
        # species-specific thresholds:
        "--min_largest_contig", str(species_params["min_largest_contig"]),
        "--max_contig_no",      str(species_params["max_contig_no"]),
        "--genome_min",         str(species_params["genome_min"]),
        "--genome_max",         str(species_params["genome_max"]),
        "--n50_min",            str(species_params["n50_min"]),
        "--hspident",           str(species_params["hspident"]),
        "--locusnlimit",        str(species_params["locusnlimit"]),
        "--snpwindow",          str(species_params["snpwindow"]),
        "--densitylim",         str(species_params["densitylim"]),
        "--refsize",            str(species_params["refsize"]),
        "--blastident",         str(species_params["blastident"]),
    ]
    # Optional passthroughs (e.g. --kraken_db) if provided
    if extra:
        for k, v in extra.items():
            if v is None:
                continue
            k = k.strip()
            if not k.startswith("--"):
                k = f"--{k}"
            cmd.extend([k, str(v)])
    return cmd

def run_one(cmd: list, dry_run: bool = False) -> int:
    print("\n>>>", " ".join(shlex.quote(p) for p in cmd))
    if dry_run:
        return 0
    proc = subprocess.run(cmd)
    return proc.returncode

# -------- main --------
def main():
    p = argparse.ArgumentParser(
        description="Iterate allele_file_details.tsv and run reads_to_alleles.py per line."
    )
    p.add_argument("--details", default="/data/allele_file_details.tsv",
                   help="Path to the TSV file with 2 columns: strainid<TAB>input_name_or_pair")
    p.add_argument("--reads-dir", default="/data/reads", help="Directory containing read files")
    p.add_argument("--assemblies-dir", default="/data/assemblies", help="Directory containing assemblies")
    p.add_argument("--refalleles", default="/species_specific_alleles/Xcitri_intact_alleles.fasta",
                   help="Static refalleles path")
    p.add_argument("--outpath", default="/data/alleles",
                   help="Static output directory (will be used by reads_to_alleles.py)")
    p.add_argument("--settings", default="/settings/settings_template.py",
                   help="Path to settings_template.py that defines SPECIES_SEROVAR")
    p.add_argument("--species-key", default="Xcitri",
                   help="Key in SPECIES_SEROVAR to use (e.g. 'Xcitri')")
    p.add_argument("--reads-to-alleles", default="./scripts/reads_to_alleles.py",
                   help="Path to reads_to_alleles.py")
    p.add_argument("--python", default=sys.executable,
                   help="Python interpreter to use for reads_to_alleles.py")
    p.add_argument("--threads", type=int, default=8,
                   help="Threads to pass through to reads_to_alleles.py")
    p.add_argument("--dry-run", action="store_true",
                   help="Print commands without executing")
    # Optional passthroughs commonly used by reads_to_alleles.py; add more if needed
    p.add_argument("--kraken-db", dest="kraken_db", default=None,
                   help="Optional: path for --kraken_db passthrough")
    p.add_argument("--force", dest="force", action="store_true",
                   help="Optional: pass --force to overwrite outputs if supported downstream")
    args = p.parse_args()

    # Load species params
    species_map = extract_species_serovar(args.settings)
    species_params = pick_species_block(species_map, args.species_key)

    # Ensure required directories exist
    for d in (args.reads_dir, args.assemblies_dir):
        if not os.path.isdir(d):
            print(f"Warning: directory not found: {d}", file=sys.stderr)
    if not os.path.isdir(args.outpath):
        os.makedirs(args.outpath, exist_ok=True)

    # Optional passthroughs
    extra = {"kraken_db": args.kraken_db}
    if args.force:
        extra["force"] = ""  # flag-only; value-less

    # Iterate TSV
    if not os.path.isfile(args.details):
        sys.exit(f"Details file not found: {args.details}")

    failures = 0
    total = 0

    with open(args.details, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = re.split(r"\t+", line)
            if len(parts) < 2:
                print(f"Skipping line {line_no}: expected 2 columns, got {len(parts)} -> {line}", file=sys.stderr)
                continue

            strainid, name_or_list = parts[0].strip(), parts[1].strip()
            try:
                intype, input_value = resolve_input_paths(name_or_list, args.reads_dir, args.assemblies_dir)
            except Exception as e:
                failures += 1
                print(f"[{strainid}] Input resolution failed: {e}", file=sys.stderr)
                continue

            # Build and run the command
            cmd = build_command(
                args.python,
                args.reads_to_alleles,
                strainid,
                intype,
                input_value,
                args.threads,
                species_params,
                args.outpath,
                args.refalleles,
                extra=extra,
            )

            # Remove value for flag-only extras (e.g. --force) in final argv
            # (we added "" as placeholder above)
            cleaned = []
            skip_empty = False
            for token in cmd:
                if skip_empty:
                    skip_empty = False
                    continue
                if token == "--force" and "" in cmd:
                    cleaned.append("--force")
                    skip_empty = True
                elif token != "":
                    cleaned.append(token)

            rc = run_one(cleaned, dry_run=args.dry_run)
            total += 1
            if rc != 0:
                failures += 1
                print(f"[{strainid}] reads_to_alleles.py exited with code {rc}", file=sys.stderr)

    ok = total - failures
    print(f"\nDone. Ran {total} jobs: {ok} ok, {failures} failed.")
    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()
