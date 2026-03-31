#!/bin/bash
# Dependencias do sistema para SPYN + Quantum ESPRESSO 7.4.1 (Debian/Ubuntu/Mint)

set -e

echo "Instalando dependencias do sistema..."
sudo apt-get install -y \
    gawk \
    gfortran \
    wget \
    liblapack-dev \
    libblas-dev \
    libscalapack-mpi-dev \
    openmpi-bin \
    libopenmpi-dev \
    xterm \
    openbabel \
    jmol \
    python3-dev \
    python3-pip

echo "Instalando dependencias Python..."
pip3 install --break-system-packages PyQt5 matplotlib pandas scipy numpy 2>/dev/null || \
pip3 install PyQt5 matplotlib pandas scipy numpy





