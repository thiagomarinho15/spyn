# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPYN is a Python/PyQt5 desktop application for NMR crystallography workflows. It provides a GUI for four interconnected tasks: conformational search (OpenBabel genetic algorithm), Boltzmann population analysis, solid-state NMR via Quantum ESPRESSO (GIPAW), and spectral visualization.

## Commands

### Development Setup
```bash
conda env create -f environment.yml && conda activate spyn-env
pip install -e .
```

### Run Tests
```bash
python3 -m pytest tests/ -v --cov=spyn --cov-report=term-missing
```

### Run a Single Test File
```bash
python3 -m pytest tests/test_boltzmann.py -v
```

### Run the GUI
```bash
cd code/spyn && python3 spyn_main.py
```

### Run Headless Example (no Quantum ESPRESSO required)
```bash
cd examples/lamivudine && python3 run_example.py
```

### Run the Graphical Installer
```bash
cd Spyn_2.0_alpha && python3 install_ui.py
```

## Architecture

### Core Separation of Concerns

`code/spyn/spyn_core.py` contains **all pure, GUI-independent functions**. This is the only module covered by CI tests — PyQt5 is not installed in CI. All new business logic must go here with corresponding tests. Coverage must stay ≥ 80%.

Key functions in `spyn_core.py`:
- `boltzmann_distribution(energies, T, unit)` — population fractions from conformer energies
- `lorentzian(x_array, peaks, A, width)` — Lorentzian lineshape for NMR spectra
- `lorentzian_smoothed(...)` — adds Savitzky-Golay smoothing (51-point window)
- `parse_gipaw_output(text, element)` — extract σ_iso from Quantum ESPRESSO GIPAW output
- `parse_giao_output(text, element)` — extract σ_iso from Gaussian GIAO `.log` files
- `sigma_to_delta(sigma_values, reference_sigma)` — shielding → chemical shift: δ = σ_ref − σ_iso

### GUI Layer

`spyn_main.py` is the QMainWindow. The UI is defined in `spynUixml.ui` (Qt Designer) and auto-generated into `spyn_ui.py` — **never edit `spyn_ui.py` by hand**. To change the UI, edit `spynUixml.ui` and regenerate.

Each tab is a separate module: `boltz.py`, `csGA.py`, `energy.py`, `pwscfnmr.py`, `plots.py`. These are GUI classes that call `spyn_core.py` functions.

### External Process Integration

Long-running tasks (`pw.x`, `gipaw.x`, `obabel`, `obenergy`) are launched via `QProcess` or `subprocess.Popen`. `xterm` is used for real-time QE terminal output. `killprocess.py` handles subprocess termination.

### Test Fixtures

`tests/conftest.py` provides shared fixtures that load example data from `code/spyn/examples/` (GIPAW output, GIAO output, conformer SDF files).

## Installer Architecture

`Spyn_2.0_alpha/install_ui.py` is the graphical installer. It:
1. Bootstraps `xterm` + `python3-pyqt5` before showing the GUI
2. Extracts `spyn.tar.gz` (4 MB — no QE sources bundled)
3. Runs `install_spyn.py` inside an xterm which downloads and compiles QE 7.4.1 + GIPAW 7.3.1 from GitHub

The installer runs compilation in a background `QThread` so the log panel stays live. QE is compiled with `--disable-parallel` (serial build, simpler dependency tree). GIPAW uses the external module `qe-gipaw 7.3.1` via `--with-qe-source`.

If the download/compilation was interrupted, re-running `install_spyn.py` is safe — it skips already-downloaded archives and already-extracted directories.

## Key Constraints

- **Python ≥ 3.9** — required for `np.trapezoid` (NumPy 2.0)
- **Linux only** — targets Debian/Ubuntu/Mint; no Windows/macOS support
- **GUI modules excluded from coverage** — only `spyn_core.py` and `__init__.py` are measured
- **CI does not install PyQt5** — all imports in test files must be PyQt5-free
- **QE version** — installer targets QE 7.4.1 + GIPAW 7.3.1 (requires internet access during install)
