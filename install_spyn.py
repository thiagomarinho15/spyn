#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPYN build script — baixa e compila Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1
Executado automaticamente pelo instalador grafico (install_ui.py).
"""

import subprocess
import os
import sys


def run(cmd, desc=None):
    if desc:
        print(f"\n>>> {desc}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n[ERRO] Falhou (codigo {result.returncode}):\n  {cmd}")
        sys.exit(result.returncode)


nproc   = subprocess.getoutput('nproc')
pwd     = subprocess.getoutput('pwd')
qe_dir  = f"{pwd}/qe"

os.makedirs(qe_dir, exist_ok=True)

print("=" * 60)
print("  SPYN — Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1")
print("=" * 60)

# Passo 1 — dependencias do sistema
run(f"bash '{pwd}/dependency.sh'",
    "Passo 1/5 — Instalando dependencias do sistema...")

# Passo 2 — baixar e compilar Quantum ESPRESSO 7.3.1
qe_archive = f"{qe_dir}/qe-7.3.1-source.tar.gz"
qe_src     = f"{qe_dir}/q-e-qe-7.3.1"
qe_url     = "https://github.com/QEF/q-e/archive/refs/tags/qe-7.3.1.tar.gz"

if not os.path.exists(qe_archive):
    run(f"wget -c '{qe_url}' -O '{qe_archive}'",
        "Passo 2/5 — Baixando Quantum ESPRESSO 7.3.1...")
else:
    print("\n>>> Passo 2/5 — Arquivo ja existe, pulando download do QE.")

if not os.path.isdir(qe_src):
    run(f"tar -xzf '{qe_archive}' -C '{qe_dir}/'",
        "Passo 2/5 — Extraindo Quantum ESPRESSO 7.3.1...")

run(
    f"cd '{qe_src}' && "
    "./configure "
    "FFLAGS='-O2 -fallow-argument-mismatch -cpp' "
    "F90FLAGS='-O2 -fallow-argument-mismatch -cpp' "
    "FC='gfortran' CC='gcc' F77='gfortran' MPIF90='mpif90'",
    "Passo 2/5 — Configurando Quantum ESPRESSO (com suporte MPI)..."
)
# Limita paralelismo a 4 para evitar race condition nos arquivos .mod
nproc_qe = max(1, min(int(nproc), 4))
run(
    f"make -j{nproc_qe} pw -C '{qe_src}' 2>&1 | tee '{qe_dir}/compile_pw.log'",
    f"Passo 2/5 — Compilando pw.x com {nproc_qe} nucleos (20-40 min)..."
)

# Passo 3 — baixar e compilar GIPAW 7.3.1
gipaw_archive = f"{qe_dir}/qe-gipaw-7.3.1.tar.gz"
gipaw_src     = f"{qe_dir}/qe-gipaw-7.3.1"
gipaw_url     = "https://github.com/dceresoli/qe-gipaw/archive/refs/tags/7.3.1.tar.gz"

if not os.path.exists(gipaw_archive):
    run(f"wget -c '{gipaw_url}' -O '{gipaw_archive}'",
        "Passo 3/5 — Baixando GIPAW 7.3.1...")
else:
    print("\n>>> Passo 3/5 — Arquivo ja existe, pulando download do GIPAW.")

if not os.path.isdir(gipaw_src):
    run(f"tar -xzf '{gipaw_archive}' -C '{qe_dir}/'",
        "Passo 3/5 — Extraindo GIPAW 7.3.1...")

run(
    f"cd '{gipaw_src}' && "
    f"./configure --with-qe-source='{qe_src}' "
    "FFLAGS='-O2 -fallow-argument-mismatch' "
    "F90FLAGS='-O2 -fallow-argument-mismatch -x f95-cpp-input'",
    "Passo 3/5 — Configurando GIPAW..."
)
run(
    f"make -C '{gipaw_src}' 2>&1 | tee '{qe_dir}/compile_gipaw.log'",
    "Passo 3/5 — Compilando gipaw.x (5–10 min)..."
)

# Passo 4 — instalar binarios em /usr/bin
run(f"bash '{pwd}/simbolic.sh'",
    "Passo 4/5 — Instalando executaveis em /usr/bin...")

# Passo 5 — criar diretorio tmp necessario para o SPYN
tmp_dir = f"{pwd}/tmp"
os.makedirs(tmp_dir, exist_ok=True)
print(f"\n>>> Passo 5/5 — Diretorio tmp criado em {tmp_dir}")

# Verificacao final
print("\n" + "=" * 60)
pw_ok    = os.path.exists(f"{qe_src}/bin/pw.x")
gipaw_ok = os.path.exists(f"{gipaw_src}/bin/gipaw.x")


if pw_ok and gipaw_ok:
    print("  OK  pw.x    compilado com sucesso")
    print("  OK  gipaw.x compilado com sucesso")
    print(f"\n  Instalacao concluida! Execute o SPYN:")
    print(f"    cd {pwd} && python3 spyn_main.py")
else:
    if not pw_ok:
        print(f"  ERRO  pw.x nao encontrado — veja: {qe_dir}/compile_pw.log")
    if not gipaw_ok:
        print(f"  ERRO  gipaw.x nao encontrado — veja: {qe_dir}/compile_gipaw.log")
    sys.exit(1)

print("=" * 60)

