#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def main():
    # Check if docker is installed
    if not shutil.which("docker"):
        sys.stderr.write("Error: 'docker' is required to run this script and is not installed or not in PATH.\n")
        sys.exit(1)

    # Check if docker compose is available
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        sys.stderr.write("Error: 'docker compose' is required to run this script and is not available.\n")
        sys.exit(1)

    # Get UID and GID of current user
    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError:
        sys.stderr.write("Error: os.getuid/os.getgid not available on this platform. MGT-Xcitri is designed to run on Mac, Linux and Windows Subsystem for Linux systems.\n")
        sys.exit(1)

    # Build docker compose command
    cmd = [
        "docker", "compose", "run", "--rm",
        "-e", f"UID={uid}",
        "-e", f"GID={gid}",
        "--user", f"{uid}:{gid}",
        "alleles"
    ] + sys.argv[1:]  # Forward all arguments

    # Run command and replace current process (like exec in bash)
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        sys.stderr.write("Error: failed to execute docker command.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
