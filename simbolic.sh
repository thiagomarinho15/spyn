#!/bin/bash
# Copies compiled binaries from QE 7.3.1 + GIPAW 7.3.1 to /usr/bin

set -e

QE_BIN="$PWD/qe/q-e-qe-7.3.1/bin/pw.x"
GIPAW_BIN="$PWD/qe/qe-gipaw-7.3.1/bin/gipaw.x"

if [ ! -f "$QE_BIN" ]; then
    echo "[ERROR] pw.x not found at: $QE_BIN"
    exit 1
fi

if [ ! -f "$GIPAW_BIN" ]; then
    echo "[ERROR] gipaw.x not found at: $GIPAW_BIN"
    exit 1
fi

sudo cp "$QE_BIN"    /usr/bin/pw
sudo cp "$GIPAW_BIN" /usr/bin/gipaw

echo "Executables installed:"
which pw && which gipaw
