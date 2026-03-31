#!/bin/bash
# Copia os binarios compilados do QE 7.3.1 + GIPAW 7.3.1 para /usr/bin

set -e

QE_BIN="$PWD/qe/q-e-qe-7.3.1/bin/pw.x"
GIPAW_BIN="$PWD/qe/qe-gipaw-7.3.1/bin/gipaw.x"

if [ ! -f "$QE_BIN" ]; then
    echo "[ERRO] pw.x nao encontrado em: $QE_BIN"
    exit 1
fi

if [ ! -f "$GIPAW_BIN" ]; then
    echo "[ERRO] gipaw.x nao encontrado em: $GIPAW_BIN"
    exit 1
fi

sudo cp "$QE_BIN"    /usr/bin/pw
sudo cp "$GIPAW_BIN" /usr/bin/gipaw

echo "Executaveis instalados:"
which pw && which gipaw
