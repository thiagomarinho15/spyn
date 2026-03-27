[![CI](https://github.com/jeffrichardchemistry/spyn/actions/workflows/ci.yml/badge.svg)](https://github.com/jeffrichardchemistry/spyn/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4019023.svg)](https://doi.org/10.5281/zenodo.4019023)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

# SPYN

**SPYN** is an open-source Python/PyQt5 desktop application for NMR crystallography workflows. It provides a unified graphical interface for four interconnected tasks that typically require separate tools and manual scripting:

1. **Conformational search** — genetic algorithm via OpenBabel to generate and rank conformer ensembles from CIF, MOL, or SDF input files.
2. **Boltzmann distribution** — population analysis of conformers at a user-defined temperature (kcal/mol or kJ/mol), with automatic import from the conformer search output.
3. **Solid-state NMR (GIPAW)** — automated generation of Quantum ESPRESSO SCF and GIPAW input files from CIF structures, execution monitoring, and output parsing to extract isotropic shielding tensors (σ_iso).
4. **Spectral visualisation** — conversion of calculated σ_iso to chemical shifts (δ = σ_ref − σ_iso), Lorentzian broadening with Savitzky-Golay smoothing, and overlay of theoretical and experimental spectra (CSV import).

SPYN reduces a typical GIPAW NMR workflow from ≥ 11 manual command-line steps to 6 GUI interactions, making solid-state NMR calculations accessible to researchers without extensive computational chemistry expertise.

---

## Installation and setup

### Overview

A distinctive feature of SPYN is its **self-contained graphical installer** (`install_ui.py`), which fully automates an otherwise complex, multi-tool setup procedure. Installing a working Quantum ESPRESSO + GIPAW environment manually requires resolving MPI, Fortran, and linear-algebra dependencies, compiling two separate codebases from source, and creating system-wide executable links — a process that routinely takes experienced users 30–60 minutes and presents a significant barrier to adoption.

SPYN eliminates this barrier entirely: a single command opens a graphical window, the user selects a directory and clicks **Install**, and the complete environment — system packages, Python dependencies, QE compilation, GIPAW compilation, and desktop integration — is configured without any further intervention.

> **No other open-source GIPAW or NMR crystallography tool provides a comparable one-command graphical installer.** Tools such as CCP-NC's `soprano`/`magresview` require manual environment setup; the Quantum ESPRESSO distribution itself provides no GUI-based installation mechanism. SPYN's installer is therefore both a usability contribution and a reproducibility mechanism: any researcher on a supported Debian/Ubuntu/Mint system can reach a working state from a fresh clone with three commands and six mouse clicks.

### Quick start

```bash
git clone https://github.com/jeffrichardchemistry/spyn.git
cd spyn/Spyn_2.0_alpha
python3 install_ui.py
```

A graphical window opens immediately. Select the destination directory, click **Install**, and the automated pipeline runs to completion.

### What `install_ui.py` does — step by step

The installer executes a **two-stage automated pipeline** that requires no further user input after the initial directory selection, except for the system root password when `apt-get` prompts for package installation.

#### Stage 1 — Graphical bootstrap (runs before the window opens)

Before displaying any interface, `install_ui.py` silently ensures its own runtime prerequisites are met:

```
python3 install_ui.py
  │
  ├─ [pre-GUI]  sudo apt install xterm
  ├─ [pre-GUI]  sudo apt-get install python3-pip python3-dev python3-pyqt5
  │
  └─ PyQt5 dialog opens
       ├── QLineEdit       — destination directory path (with placeholder text)
       ├── QPushButton "Procurar..."  — opens QFileDialog directory browser
       ├── QProgressBar    — indeterminate spinner during installation
       ├── QTextEdit       — live installation log (dark-themed monospace)
       └── QPushButton "Instalar"  — triggers Stage 2
```

This bootstrapping strategy means `install_ui.py` can be run on a completely bare Python 3 system: it installs its own GUI dependency before attempting to import it.

#### Stage 2 — Full environment build (triggered by clicking Instalar)

The installation runs in a background thread so the interface stays responsive. A live log displays each step as it executes.

```
User clicks Instalar
  │
  ├─ 1. Extract spyn.tar.gz  ──────────────────────────────────────────────────────
  │       tar -xzvf spyn.tar.gz -C <chosen_directory>
  │       Unpacks the SPYN source tree, pseudopotentials, and auxiliary scripts.
  │       (QE sources are downloaded during installation — not bundled.)
  │
  ├─ 2. Write runtime path configuration  ─────────────────────────────────────────
  │       Creates spyndir.py inside the installation directory.
  │       This module exposes the absolute installation path to all SPYN modules
  │       at runtime, eliminating hardcoded paths and enabling installation to
  │       any user-chosen location.
  │
  ├─ 3. Write launcher script  ────────────────────────────────────────────────────
  │       Creates spyn.sh:
  │           #!/bin/bash
  │           cd <install_dir>/spyn && python3 spyn_main.py
  │       This script is used both by the desktop entry and by direct invocation.
  │
  ├─ 4. Open xterm → run install_spyn.py  ─────────────────────────────────────────
  │       A terminal window opens and executes the full build chain:
  │
  │       install_spyn.py
  │         │
  │         ├─ dependency.sh
  │         │     sudo apt-get install:
  │         │       gawk  gfortran  wget
  │         │       liblapack-dev  libblas-dev  libscalapack-mpi-dev
  │         │       openmpi-bin  libopenmpi-dev
  │         │       xterm  openbabel  jmol  python3-dev  python3-pip
  │         │     pip3 install:
  │         │       PyQt5  matplotlib  pandas  scipy  numpy
  │         │
  │         ├─ Quantum ESPRESSO 7.3.1
  │         │     wget qe-7.3.1.tar.gz  (downloaded from GitHub)
  │         │     ./configure --disable-parallel
  │         │         FFLAGS/F90FLAGS="-O2 -fallow-argument-mismatch"
  │         │     make -j$(nproc) pw          ← uses all available CPU cores
  │         │     Produces:  bin/pw.x
  │         │
  │         ├─ GIPAW 7.3.1
  │         │     wget qe-gipaw-7.3.1.tar.gz  (downloaded from GitHub)
  │         │     ./configure --with-qe-source=<qe-7.3.1 path>
  │         │     make                        ← produces bin/gipaw.x
  │         │
  │         └─ simbolic.sh  —  system-wide executable links
  │               sudo cp bin/pw.x    /usr/bin/pw
  │               sudo cp bin/gipaw.x /usr/bin/gipaw
  │               Makes pw and gipaw callable from any working directory.
  │
  └─ 5. Desktop integration  ──────────────────────────────────────────────────────
          Creates spyn.desktop (XDG Desktop Entry spec):
            Name=Spyn
            Exec=<install_dir>/spyn/spyn.sh
            Icon=<install_dir>/spyn/fig/spyn.png
            Type=Application
            Categories=Science;Education;

          Runs permissionDE.sh:
            sudo chmod a+xrw spyn.desktop
            sudo chmod +x spyn.sh
            sudo cp spyn.desktop /usr/share/applications/spyn.desktop

          After this step, SPYN appears as a named application with an icon
          in the system applications menu (GNOME, KDE, XFCE, etc.).
```

#### Summary table

| Phase | Automated action | Manual equivalent |
|-------|-----------------|-------------------|
| Pre-GUI bootstrap | Install `xterm`, `python3-pyqt5` via `apt` | `sudo apt install ...` |
| Archive extraction | Extract SPYN source tree + assets | `tar -xzvf ...` |
| Path configuration | Generate `spyndir.py` with installation path | Edit source file manually |
| System packages | Install 13 system dependencies via `apt-get` | Multiple `sudo apt install` calls |
| Python packages | Install 5 Python packages via `pip3` | `pip3 install ...` |
| QE 7.3.1 download | `wget` source from GitHub | Manual download |
| QE compilation | Configure + compile `pw.x` | ~20–40 min expert procedure |
| GIPAW 7.3.1 download | `wget` source from GitHub | Manual download |
| GIPAW compilation | Configure + compile `gipaw.x` against QE 7.3.1 | ~5–10 min expert procedure |
| System links | `/usr/bin/pw`, `/usr/bin/gipaw` | `sudo cp` + verify `$PATH` |
| Desktop integration | `.desktop` entry + icon in system menu | Manual XDG entry creation |

**Total user actions required: 6** (run command, open dialog, select directory, click Instalar, enter root password once, launch SPYN from menu).

**Total automated actions: 11 phases, covering ≥ 25 individual commands** that would otherwise be executed and verified manually.

### System requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | ≥ 3.9 | 3.9 or newer |
| PyQt5 | ≥ 5.12 | GUI framework (installed automatically) |
| NumPy / SciPy / Pandas / Matplotlib | see `requirements.txt` | Installed automatically |
| OpenBabel | ≥ 3.0 | Installed automatically (`obabel`, `obenergy`) |
| Quantum ESPRESSO | 7.3.1 | Downloaded and compiled automatically |
| GIPAW | 7.3.1 | Downloaded and compiled automatically |
| xterm | any | Installed automatically; terminal for QE subprocess |
| Jmol | any | Installed automatically; optional 3D molecular viewer |
| OS | Linux (Debian/Ubuntu/Mint) | Tested: Ubuntu 22–24, Debian 11/12, Mint 21+ |

### Manual installation (non-Debian systems)

For RPM-based distributions (Fedora, openSUSE, CentOS) or systems where the automated installer cannot be used, full step-by-step instructions including QE and GIPAW compilation are provided in [docs/installation.md](docs/installation.md).

---

## Quickstart — reproducible example (no QE required)

To verify the pure-Python components (conformer ranking, Boltzmann populations, spectral simulation) without a QE installation:

```bash
cd examples/lamivudine
python run_example.py
# → prints Boltzmann populations + 13C chemical shifts
# → saves example_spectrum.png
```

This headless script is also used by the CI pipeline on every push to confirm numerical reproducibility across Python 3.9, 3.10, and 3.11.

## Quickstart — full GUI workflow

```bash
cd code/spyn
python spyn_main.py
```

Then follow the four tabs in sequence:
**Conformational Searching → Boltzmann Distribution → ss-NMR → Spectro-NMR**.

See [docs/quickstart.md](docs/quickstart.md) for a step-by-step tutorial with screenshots.

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/installation.md](docs/installation.md) | Full installation guide — automated and manual procedures |
| [docs/quickstart.md](docs/quickstart.md) | Step-by-step walkthrough of all four GUI tabs |
| [docs/modules/spyn_core.md](docs/modules/spyn_core.md) | API reference for the pure-Python functions (`spyn_core.py`) |
| [docs/comparison.md](docs/comparison.md) | Feature comparison vs CCP-NC toolbox and magresview |
| [CHANGELOG.md](CHANGELOG.md) | Version history in Keep-a-Changelog format |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## Testing and continuous integration

SPYN includes a suite of 34 unit tests covering all pure-Python functions (Boltzmann statistics, Lorentzian broadening, GIPAW output parsing, and GIAO output parsing), with 92.86 % line coverage on `spyn_core.py`.

```bash
pytest tests/ -v --cov=spyn
```

Tests run automatically via GitHub Actions on every push and pull request, across Python 3.9, 3.10, and 3.11 on Ubuntu.

| Test module | Cases | Coverage |
|-------------|-------|----------|
| `test_boltzmann.py` | 10 | 100 % of `boltzmann_distribution` |
| `test_lorentz.py` | 7 | 100 % of `lorentzian` |
| `test_parser_gipaw.py` | 8 | ≥ 80 % of `parse_gipaw_output` |
| `test_parser_giao.py` | 9 | ≥ 80 % of `parse_giao_output` |
| **Total** | **34** | **92.86 % (spyn_core.py)** |

---

## How to cite

If you use SPYN in published work, please cite:

```bibtex
@software{spyn2020,
  author  = {Dias da Silva, Jefferson Richard and
             Keng Queiroz Junior, Luiz Henrique},
  title   = {{SPYN}: An Open-Source Python Platform with GUI
             for NMR Crystallography},
  year    = {2020},
  doi     = {10.5281/zenodo.4019023},
  url     = {https://github.com/jeffrichardchemistry/spyn},
  license = {GPL-3.0}
}
```

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.
