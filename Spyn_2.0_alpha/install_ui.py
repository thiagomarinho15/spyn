# -*- coding: utf-8 -*-
"""
SPYN Installer — graphical installation interface
Installs SPYN + Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1 automatically.

Usage:
    python3 install_ui.py
"""

import subprocess
import sys
import os

# Bootstrap: ensure system packages are available before importing PyQt5
_bootstrap_pkgs = ['xterm', 'python3-pip', 'python3-dev', 'python3-pyqt5', 'python3-pyqt5.qtsvg']
print("[bootstrap] Repairing dpkg state (if needed)...", flush=True)
subprocess.run(['sudo', 'dpkg', '--configure', '-a'], capture_output=False)
print("[bootstrap] Running apt-get update...", flush=True)
_r = subprocess.run(['sudo', 'apt-get', 'update', '-qq'], capture_output=False)
if _r.returncode != 0:
    print(f"[bootstrap] WARNING: apt-get update failed (code {_r.returncode})", flush=True)
print(f"[bootstrap] Installing: {' '.join(_bootstrap_pkgs)}", flush=True)
_r = subprocess.run(
    ['sudo', 'apt-get', 'install', '-y'] + _bootstrap_pkgs,
    capture_output=False
)
if _r.returncode != 0:
    print(f"[bootstrap] ERROR: apt-get install failed (code {_r.returncode})", flush=True)
    sys.exit(1)
print("[bootstrap] Bootstrap packages OK.", flush=True)

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QFrame
)


# ──────────────────────────────────────────────────────────────
# Thread de instalacao (evita travar a interface)
# ──────────────────────────────────────────────────────────────

class InstallThread(QThread):
    log     = pyqtSignal(str)
    status  = pyqtSignal(str)
    done    = pyqtSignal(bool)

    def __init__(self, install_dir, installer_dir):
        super().__init__()
        self.install_dir   = install_dir
        self.installer_dir = installer_dir

    def run(self):
        try:
            spyn_dir = os.path.join(self.install_dir, 'spyn')
            archive  = os.path.join(self.installer_dir, 'spyn.tar.gz')

            # 1 — install system and Python dependencies
            self.status.emit("Repairing dpkg state...")
            self.log.emit("→ Running dpkg --configure -a (safe no-op if not needed)...")
            subprocess.run(['sudo', 'dpkg', '--configure', '-a'],
                           capture_output=True, text=True)

            self.status.emit("Updating package list...")
            self.log.emit("→ Running apt-get update...")
            r = subprocess.run(
                ['sudo', 'apt-get', 'update', '-qq'],
                capture_output=True, text=True
            )
            if r.returncode != 0:
                self.log.emit(f"[WARNING] apt-get update failed (code {r.returncode}): {r.stderr.strip()}")

            self.status.emit("Installing system dependencies...")
            self.log.emit("→ Installing Debian packages (apt)...")
            apt_packages = [
                'gawk', 'gfortran', 'openmpi-bin', 'openmpi-doc',
                'libopenmpi-dev', 'xterm', 'openbabel', 'jmol',
                'python3-dev', 'python3-pip', 'python3-pyqt5',
                'python3-pyqt5.qtsvg',
            ]
            r = subprocess.run(
                ['sudo', 'apt-get', 'install', '-y'] + apt_packages,
                capture_output=True, text=True
            )
            if r.returncode != 0:
                self.log.emit(f"[WARNING] apt-get install returned code {r.returncode}: {r.stderr.strip()}")
            else:
                self.log.emit("   System dependencies installed.")

            self.status.emit("Installing Python dependencies (pip)...")
            self.log.emit("→ Installing Python packages (pip)...")
            # numpy>=2.0 is required for np.trapezoid; pip ensures the correct version
            # since apt ships numpy 1.x on Debian 12.
            pip_packages = ['numpy>=2.0', 'matplotlib', 'pandas', 'scipy']
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--break-system-packages'] + pip_packages,
                capture_output=True, text=True
            )
            if r.returncode != 0:
                self.log.emit(f"[WARNING] pip returned code {r.returncode}: {r.stderr.strip()}")
            else:
                self.log.emit("   Python dependencies installed.")

            # 3 — extract files
            self.status.emit("Extracting SPYN files...")
            self.log.emit(f"→ Extracting {archive} to {self.install_dir}/")
            r = subprocess.run(
                f"tar -xzvf '{archive}' -C '{self.install_dir}'",
                shell=True, capture_output=True, text=True
            )
            if r.returncode != 0:
                self.log.emit(f"[ERROR] {r.stderr}")
                self.done.emit(False)
                return

            # 4 — write path configuration (spyndir.py)
            self.status.emit("Configuring installation paths...")
            self.log.emit(f"→ Creating spyndir.py in {spyn_dir}/")
            with open(os.path.join(spyn_dir, 'spyndir.py'), 'w') as f:
                f.write(
                    "class Spyndir():\n"
                    "   def __init__(self):\n"
                    f"       self.spyndir = '{spyn_dir}'\n"
                )

            # 5 — create launcher script (spyn.sh)
            launcher = os.path.join(spyn_dir, 'spyn.sh')
            with open(launcher, 'w') as f:
                f.write(f"#!/bin/bash\ncd '{spyn_dir}' && python3 spyn_main.py\n")

            # 6 — open terminal and compile QE + GIPAW
            self.status.emit("Compiling Quantum ESPRESSO 7.3.1 + GIPAW 7.3.1...")
            self.log.emit("→ Opening terminal for compilation (30–60 min)...")
            self.log.emit("   Follow the progress in the terminal window.")
            subprocess.run(
                f"xterm -title 'SPYN — Compilation' -fa 'Monospace' -fs 10 "
                f"-e 'cd \"{spyn_dir}\" && python3 install_spyn.py; "
                f"echo; echo Press ENTER to close.; read'",
                shell=True
            )

            # 7 — application menu entry
            self.status.emit("Creating application menu entry...")
            self.log.emit("→ Creating spyn.desktop and permissions...")
            desktop_entry = (
                "[Desktop Entry]\n"
                "Name=Spyn\n"
                "GenericName=Spyn\n"
                "Comment=GUI for NMR Crystallography\n"
                f"Exec={launcher}\n"
                "Terminal=false\n"
                "Type=Application\n"
                f"Icon={spyn_dir}/fig/spyn.png\n"
                "StartupNotify=false\n"
                "Categories=Science;Education;\n"
            )
            desktop_file = os.path.join(spyn_dir, 'spyn.desktop')
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)

            perm_script = os.path.join(spyn_dir, 'permissionDE.sh')
            with open(perm_script, 'w') as f:
                f.write(
                    "#!/bin/bash\n"
                    f"sudo chmod a+xrw '{desktop_file}'\n"
                    f"sudo chmod +x '{launcher}'\n"
                    f"sudo cp '{desktop_file}' /usr/share/applications/spyn.desktop\n"
                )
            subprocess.run(
                f"xterm -title 'SPYN — Permissions' -e "
                f"'sh \"{perm_script}\" && exit; bash'",
                shell=True
            )

            self.log.emit("→ Installation completed successfully!")
            self.done.emit(True)

        except Exception as exc:
            self.log.emit(f"[UNEXPECTED ERROR] {exc}")
            self.done.emit(False)


# ──────────────────────────────────────────────────────────────
# Janela principal do instalador
# ──────────────────────────────────────────────────────────────

class InstallerWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.installer_dir = os.path.dirname(os.path.abspath(__file__))
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("SPYN Installer")
        self.setMinimumWidth(620)
        self.setMinimumHeight(520)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(20, 20, 20, 20)

        # --- Cabecalho ---
        title = QLabel("SPYN")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a1a2e;")
        subtitle = QLabel("NMR Crystallography Software — Installer v2.0.0")
        subtitle.setStyleSheet("font-size: 13px; color: #555;")
        root.addWidget(title)
        root.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #ccc;")
        root.addWidget(sep)

        # --- Informacoes ---
        info = QLabel(
            "This installer will automatically configure:\n"
            "  • System dependencies (via apt)\n"
            "  • Quantum ESPRESSO 7.3.1  (full compilation)\n"
            "  • GIPAW 7.3.1 module\n"
            "  • Application menu shortcut\n\n"
            "Estimated time: 40–60 minutes (mostly compilation)."
        )
        info.setStyleSheet("font-size: 12px; color: #333; padding: 4px 0;")
        root.addWidget(info)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #ccc;")
        root.addWidget(sep2)

        # --- Selecao de diretorio ---
        dir_label = QLabel("Installation directory:")
        dir_label.setStyleSheet("font-weight: bold;")
        root.addWidget(dir_label)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Click Browse to choose a directory...")
        self.dir_input.setMinimumHeight(32)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(self.dir_input, stretch=1)
        dir_row.addWidget(self.browse_btn)
        root.addLayout(dir_row)

        # --- Status e progresso ---
        self.status_label = QLabel("Waiting for directory selection.")
        self.status_label.setStyleSheet("color: #555; font-style: italic;")
        root.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)   # modo indeterminado
        self.progress.setVisible(False)
        self.progress.setMinimumHeight(16)
        root.addWidget(self.progress)

        # --- Log ---
        log_label = QLabel("Installation log:")
        log_label.setStyleSheet("font-weight: bold;")
        root.addWidget(log_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(160)
        self.log_box.setStyleSheet(
            "font-family: 'Courier New', monospace; font-size: 11px; "
            "background: #1e1e1e; color: #d4d4d4; border-radius: 4px;"
        )
        root.addWidget(self.log_box, stretch=1)

        # --- Botao Instalar ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.install_btn = QPushButton("  Install  ")
        self.install_btn.setMinimumHeight(42)
        self.install_btn.setMinimumWidth(130)
        self.install_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; "
            "background-color: #0078d4; color: white; border-radius: 6px; }"
            "QPushButton:hover { background-color: #005fa3; }"
            "QPushButton:disabled { background-color: #aaa; }"
        )
        self.install_btn.clicked.connect(self._start_install)
        btn_row.addWidget(self.install_btn)
        root.addLayout(btn_row)

    # ----------------------------------------------------------

    def _browse(self):
        d = QFileDialog.getExistingDirectory(
            self, 'Select installation directory', os.path.expanduser('~')
        )
        if d:
            self.dir_input.setText(d)
            self.status_label.setText("Directory selected. Click Install to begin.")

    def _log(self, msg):
        self.log_box.append(msg)
        self.log_box.ensureCursorVisible()

    def _start_install(self):
        chosen = self.dir_input.text().strip()
        if not chosen:
            QMessageBox.warning(self, "No directory selected",
                                "Please choose a directory before installing.")
            return
        if not os.path.isdir(chosen):
            QMessageBox.warning(self, "Invalid directory",
                                f"The directory does not exist:\n{chosen}")
            return

        self.install_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress.setVisible(True)
        self._log(f"Starting installation in: {chosen}/spyn\n")

        self.thread = InstallThread(chosen, self.installer_dir)
        self.thread.log.connect(self._log)
        self.thread.status.connect(self.status_label.setText)
        self.thread.done.connect(self._on_done)
        self.thread.start()

    def _on_done(self, success):
        self.progress.setVisible(False)
        self.install_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

        if success:
            self.status_label.setText("Installation completed successfully!")
            QMessageBox.information(
                self, "SPYN installed",
                "SPYN was installed successfully!\n\n"
                "You can start the program from the application menu\n"
                "or by running:\n\n"
                f"  cd {self.dir_input.text()}/spyn\n"
                "  python3 spyn_main.py"
            )
        else:
            self.status_label.setText("Installation failed. See the log above.")
            QMessageBox.critical(
                self, "Installation error",
                "The installation encountered an error.\n\n"
                "Check the log in this window and the files:\n"
                "  • compile_pw.log\n"
                "  • compile_gipaw.log\n\n"
                "inside the qe/ directory of the installation."
            )


# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec_())
