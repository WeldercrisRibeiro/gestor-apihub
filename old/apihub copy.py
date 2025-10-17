import sys
import os
import subprocess
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIcon

class GerenciadorServicos(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Caminho base (ajusta conforme sua estrutura)
        self.base_dir = os.path.dirname(__file__)

        # Caminho do arquivo UI
        ui_path = os.path.join(self.base_dir, "assets", "apihub.ui")
        uic.loadUi(ui_path, self)

        # Caminhos dos arquivos BAT
        self.bats = {
            "instalar": r"C:\INFARMA\APIHUB\bats\1-instala-servicos.bat",
            "reiniciar": r"C:\INFARMA\APIHUB\bats\2-reinicia-servicos.bat",
            "excluir": r"C:\INFARMA\APIHUB\bats\3-exclui-servicos.bat"
        }

        # Caminho do arquivo .env
        self.env_path = r"C:\INFARMA\APIHUB\.env"

        # Ícone do app
        icon_path = os.path.join(self.base_dir, "assets", "apihub-white.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Conecta os botões
        #self.btnAbrirEnv.clicked.connect(self.abrir_env)
        self.btnInstalar.clicked.connect(self.instalar_servicos)
        self.btnReiniciar.clicked.connect(self.reiniciar_servicos)
        self.btnExcluir.clicked.connect(self.excluir_servicos)
        self.btnSair.clicked.connect(self.close)

    # ---------- Funções ----------
    def abrir_env(self):
        """Abre o arquivo .env no editor padrão"""
        try:
            os.startfile(self.env_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo .env:\n{e}")

    def executar_bat(self, caminho_bat):
        """Executa um arquivo .bat e exibe o resultado"""
        try:
            subprocess.run(caminho_bat, check=True, shell=True)
            QtWidgets.QMessageBox.information(self, "Sucesso", f"Arquivo executado:\n{caminho_bat}")
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Falha ao executar:\n{caminho_bat}\n\n{e}")

    def instalar_servicos(self):
        self.executar_bat(self.bats["instalar"])

    def reiniciar_servicos(self):
        self.executar_bat(self.bats["reiniciar"])

    def excluir_servicos(self):
        self.executar_bat(self.bats["excluir"])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GerenciadorServicos()
    window.show()
    sys.exit(app.exec_())
