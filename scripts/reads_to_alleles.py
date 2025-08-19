#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def detect_mounts(argv):
    """
    Scan argv for file/dir arguments, collect parent directories that exist.
    """
    mounts = set()
    skip_next = False
    for i, arg in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        # Flags with a value
        if arg in ("-i", "--input", "--refalleles", "-o", "--outpath",
                   "--kraken_db", "--tmpdir", "--pathovar_key"):
            if i + 1 < len(argv):
                val = argv[i + 1]
                skip_next = True
                for part in val.split(","):
                    p = os.path.abspath(part)
                    if os.path.exists(p):
                        mounts.add(os.path.dirname(p) if os.path.isfile(p) else p)
        else:
            # Also check if this arg itself looks like a path (doesn’t start with -)
            if not arg.startswith("-"):
                p = os.path.abspath(arg)
                if os.path.exists(p):
                    mounts.add(os.path.dirname(p) if os.path.isfile(p) else p)
    return mounts

def main():
    if not shutil.which("docker"):
        sys.stderr.write("Error: 'docker' not found in PATH.\n")
        sys.exit(1)

    try:
        subprocess.run(["docker", "compose", "version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except subprocess.CalledProcessError:
        sys.stderr.write("Error: 'docker compose' not available.\n")
        sys.exit(1)

    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError:
        sys.stderr.write("Error: os.getuid/os.getgid not available on this platform.\n")
        sys.exit(1)

    argv = sys.argv[1:]
    mounts = detect_mounts(argv)

    cmd = [
        "docker", "compose", "run", "--rm",
        "-e", f"UID={uid}",
        "-e", f"GID={gid}",
        "--user", f"{uid}:{gid}",
    ]

    for m in mounts:
        cmd += ["-v", f"{m}:{m}"]

    cmd.append("alleles")
    cmd += argv

    # Run
    try:
        sys.exit(subprocess.run(cmd).returncode)
    except FileNotFoundError:
        sys.stderr.write("Error: failed to execute docker command.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
