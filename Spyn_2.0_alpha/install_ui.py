# -*- coding: utf-8 -*-
"""
SPYN Installer — interface grafica de instalacao
Instala SPYN + Quantum ESPRESSO 7.4.1 + GIPAW 7.3.1 automaticamente.

Uso:
    python3 install_ui.py
"""

import subprocess
import sys
import os

# Bootstrap: garante que xterm e PyQt5 estejam disponiveis antes do import
subprocess.run(['sudo', 'apt', 'install', '-y', 'xterm'], capture_output=True)
subprocess.run(
    ['sudo', 'apt-get', 'install', '-y', 'python3-pip', 'python3-dev', 'python3-pyqt5'],
    capture_output=True
)

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

            # 1 — extrair arquivos
            self.status.emit("Extraindo arquivos do SPYN...")
            self.log.emit(f"→ Extraindo {archive} para {self.install_dir}/")
            r = subprocess.run(
                f"tar -xzvf '{archive}' -C '{self.install_dir}'",
                shell=True, capture_output=True, text=True
            )
            if r.returncode != 0:
                self.log.emit(f"[ERRO] {r.stderr}")
                self.done.emit(False)
                return

            # 2 — gravar configuracao de caminho (spyndir.py)
            self.status.emit("Configurando caminhos de instalacao...")
            self.log.emit(f"→ Criando spyndir.py em {spyn_dir}/")
            with open(os.path.join(spyn_dir, 'spyndir.py'), 'w') as f:
                f.write(
                    "class Spyndir():\n"
                    "   def __init__(self):\n"
                    f"       self.spyndir = '{spyn_dir}'\n"
                )

            # 3 — criar script de lancamento (spyn.sh)
            launcher = os.path.join(spyn_dir, 'spyn.sh')
            with open(launcher, 'w') as f:
                f.write(f"#!/bin/bash\ncd '{spyn_dir}' && python3 spyn_main.py\n")

            # 4 — abrir terminal e compilar QE + GIPAW
            self.status.emit("Compilando Quantum ESPRESSO 7.4.1 + GIPAW 7.3.1...")
            self.log.emit("→ Abrindo terminal para compilacao (30–60 min)...")
            self.log.emit("   Acompanhe o progresso na janela do terminal.")
            subprocess.run(
                f"xterm -title 'SPYN — Compilacao' -fa 'Monospace' -fs 10 "
                f"-e 'cd \"{spyn_dir}\" && python3 install_spyn.py; "
                f"echo; echo Pressione ENTER para fechar.; read'",
                shell=True
            )

            # 5 — entrada no menu de aplicativos
            self.status.emit("Criando entrada no menu de aplicativos...")
            self.log.emit("→ Criando spyn.desktop e permissoes...")
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
                f"xterm -title 'SPYN — Permissoes' -e "
                f"'sh \"{perm_script}\" && exit; bash'",
                shell=True
            )

            self.log.emit("→ Instalacao concluida com sucesso!")
            self.done.emit(True)

        except Exception as exc:
            self.log.emit(f"[ERRO INESPERADO] {exc}")
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
        subtitle = QLabel("NMR Crystallography Software — Instalador v2.0.0")
        subtitle.setStyleSheet("font-size: 13px; color: #555;")
        root.addWidget(title)
        root.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #ccc;")
        root.addWidget(sep)

        # --- Informacoes ---
        info = QLabel(
            "Este instalador configurara automaticamente:\n"
            "  • Dependencias do sistema (via apt)\n"
            "  • Quantum ESPRESSO 7.4.1  (compilacao completa)\n"
            "  • Modulo GIPAW 7.3.1\n"
            "  • Atalho no menu de aplicativos\n\n"
            "Tempo estimado: 40–60 minutos (maior parte na compilacao)."
        )
        info.setStyleSheet("font-size: 12px; color: #333; padding: 4px 0;")
        root.addWidget(info)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #ccc;")
        root.addWidget(sep2)

        # --- Selecao de diretorio ---
        dir_label = QLabel("Diretorio de instalacao:")
        dir_label.setStyleSheet("font-weight: bold;")
        root.addWidget(dir_label)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Clique em Procurar para escolher um diretorio...")
        self.dir_input.setMinimumHeight(32)
        self.browse_btn = QPushButton("Procurar...")
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(self.dir_input, stretch=1)
        dir_row.addWidget(self.browse_btn)
        root.addLayout(dir_row)

        # --- Status e progresso ---
        self.status_label = QLabel("Aguardando selecao de diretorio.")
        self.status_label.setStyleSheet("color: #555; font-style: italic;")
        root.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)   # modo indeterminado
        self.progress.setVisible(False)
        self.progress.setMinimumHeight(16)
        root.addWidget(self.progress)

        # --- Log ---
        log_label = QLabel("Log de instalacao:")
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
        self.install_btn = QPushButton("  Instalar  ")
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
            self, 'Selecione o diretorio de instalacao', os.path.expanduser('~')
        )
        if d:
            self.dir_input.setText(d)
            self.status_label.setText("Diretorio selecionado. Clique em Instalar para comecar.")

    def _log(self, msg):
        self.log_box.append(msg)
        self.log_box.ensureCursorVisible()

    def _start_install(self):
        chosen = self.dir_input.text().strip()
        if not chosen:
            QMessageBox.warning(self, "Diretorio nao selecionado",
                                "Por favor, escolha um diretorio antes de instalar.")
            return
        if not os.path.isdir(chosen):
            QMessageBox.warning(self, "Diretorio invalido",
                                f"O diretorio nao existe:\n{chosen}")
            return

        self.install_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress.setVisible(True)
        self._log(f"Iniciando instalacao em: {chosen}/spyn\n")

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
            self.status_label.setText("Instalacao concluida com sucesso!")
            QMessageBox.information(
                self, "SPYN instalado",
                "SPYN foi instalado com sucesso!\n\n"
                "Voce pode iniciar o programa pelo menu de aplicativos\n"
                "ou executando:\n\n"
                f"  cd {self.dir_input.text()}/spyn\n"
                "  python3 spyn_main.py"
            )
        else:
            self.status_label.setText("Instalacao falhou. Veja o log acima.")
            QMessageBox.critical(
                self, "Erro na instalacao",
                "A instalacao encontrou um erro.\n\n"
                "Verifique o log nesta janela e os arquivos:\n"
                "  • compile_pw.log\n"
                "  • compile_gipaw.log\n\n"
                "dentro do diretorio qe/ da instalacao."
            )


# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec_())
