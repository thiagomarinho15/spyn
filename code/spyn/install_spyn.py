#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPYN build script — downloads and compiles Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1
Run automatically by the graphical installer (install_ui.py).
"""

import subprocess
import os
import sys


def run(cmd, desc=None):
    if desc:
        print(f"\n>>> {desc}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n[ERROR] Failed (code {result.returncode}):\n  {cmd}")
        sys.exit(result.returncode)


nproc   = subprocess.getoutput('nproc')
pwd     = subprocess.getoutput('pwd')
qe_dir  = f"{pwd}/qe"

os.makedirs(qe_dir, exist_ok=True)

print("=" * 60)
print("  SPYN — Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1")
print("=" * 60)

# Step 1 — system dependencies
run(f"bash '{pwd}/dependency.sh'",
    "Step 1/5 — Installing system dependencies...")

# Passo 2 — baixar e compilar Quantum ESPRESSO 7.3.1
qe_archive = f"{qe_dir}/qe-7.3.1-source.tar.gz"
qe_src     = f"{qe_dir}/q-e-qe-7.3.1"
qe_url     = "https://github.com/QEF/q-e/archive/refs/tags/qe-7.3.1.tar.gz"

if not os.path.exists(qe_archive):
    run(f"wget -c '{qe_url}' -O '{qe_archive}'",
        "Step 2/5 — Downloading Quantum ESPRESSO 7.3.1...")
else:
    print("\n>>> Step 2/5 — Archive already exists, skipping QE download.")

if not os.path.isdir(qe_src):
    run(f"tar -xzf '{qe_archive}' -C '{qe_dir}/'",
        "Step 2/5 — Extracting Quantum ESPRESSO 7.3.1...")

run(
    f"cd '{qe_src}' && "
    "./configure "
    "FFLAGS='-O2 -fallow-argument-mismatch -cpp' "
    "F90FLAGS='-O2 -fallow-argument-mismatch -cpp' "
    "FC='gfortran' CC='gcc' F77='gfortran' MPIF90='mpif90'",
    "Step 2/5 — Configuring Quantum ESPRESSO (with MPI support)..."
)
# Step 1: compile base Fortran modules sequentially to avoid race conditions
# on .mod files (kinds.mod, constants.mod, etc.) that all other files depend on.
run(
    f"make -j1 -C '{qe_src}' modules 2>&1 | tee '{qe_dir}/compile_modules.log'",
    "Step 2/5 — Compiling base modules (sequential, avoids kinds.mod race condition)..."
)
# Step 2: compile pw.x with limited parallelism (max 2 to avoid memory issues on VMs)
nproc_qe = max(1, min(int(nproc), 2))
run(
    f"make -j{nproc_qe} pw -C '{qe_src}' 2>&1 | tee '{qe_dir}/compile_pw.log'",
    f"Step 2/5 — Compiling pw.x with {nproc_qe} cores (20-40 min)..."
)

# Passo 3 — baixar e compilar GIPAW 7.3.1
gipaw_archive = f"{qe_dir}/qe-gipaw-7.3.1.tar.gz"
gipaw_src     = f"{qe_dir}/qe-gipaw-7.3.1"
gipaw_url     = "https://github.com/dceresoli/qe-gipaw/archive/refs/tags/7.3.1.tar.gz"

if not os.path.exists(gipaw_archive):
    run(f"wget -c '{gipaw_url}' -O '{gipaw_archive}'",
        "Step 3/5 — Downloading GIPAW 7.3.1...")
else:
    print("\n>>> Step 3/5 — Archive already exists, skipping GIPAW download.")

if not os.path.isdir(gipaw_src):
    run(f"tar -xzf '{gipaw_archive}' -C '{qe_dir}/'",
        "Step 3/5 — Extracting GIPAW 7.3.1...")

run(
    f"cd '{gipaw_src}' && "
    f"./configure --with-qe-source='{qe_src}' "
    "FFLAGS='-O2 -fallow-argument-mismatch' "
    "F90FLAGS='-O2 -fallow-argument-mismatch -x f95-cpp-input'",
    "Step 3/5 — Configuring GIPAW..."
)
run(
    f"make -C '{gipaw_src}' 2>&1 | tee '{qe_dir}/compile_gipaw.log'",
    "Step 3/5 — Compiling gipaw.x (5–10 min)..."
)

# Step 4 — install binaries to /usr/bin
run(f"bash '{pwd}/simbolic.sh'",
    "Step 4/5 — Installing executables to /usr/bin...")

# Step 5 — create tmp directory required by SPYN
tmp_dir = f"{pwd}/tmp"
os.makedirs(tmp_dir, exist_ok=True)
print(f"\n>>> Step 5/5 — tmp directory created at {tmp_dir}")

# Final verification
print("\n" + "=" * 60)
pw_ok    = os.path.exists(f"{qe_src}/bin/pw.x")
gipaw_ok = os.path.exists(f"{gipaw_src}/bin/gipaw.x")


if pw_ok and gipaw_ok:
    print("  OK  pw.x    compiled successfully")
    print("  OK  gipaw.x compiled successfully")
    print(f"\n  Installation complete! Run SPYN:")
    print(f"    cd {pwd} && python3 spyn_main.py")
else:
    if not pw_ok:
        print(f"  ERROR  pw.x not found — see: {qe_dir}/compile_pw.log")
    if not gipaw_ok:
        print(f"  ERROR  gipaw.x not found — see: {qe_dir}/compile_gipaw.log")
    sys.exit(1)

print("=" * 60)

