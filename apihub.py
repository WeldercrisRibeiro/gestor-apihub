import sys
import os
import webbrowser
import subprocess
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QLabel,
    QStyle,
)
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets, uic, QtGui


class EnvEditorDialog(QDialog):
    """Diálogo simples para editar as chaves do .env solicitadas pelo usuário."""

    def __init__(self, env_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar configurações")
        self.env_path = env_path

        try:
            self.resize(100, 200)
            self.setMinimumWidth(300)
        except Exception:
            pass

        layout = QFormLayout(self)

        self.hostname = QLineEdit()
        self.porta = QLineEdit()
        self.banco = QLineEdit()
        self.usuario = QLineEdit()
        self.senha = QLineEdit()

        self.cod_vendedor = QLineEdit()
        self.cod_produto_servico = QLineEdit()
        self.cod_produto_entrega = QLineEdit()
        self.pagamento_entrega = QLineEdit()
        self.pagamento_online = QLineEdit()
        self.email = QLineEdit()

        layout.addRow(QLabel("HOSTNAME"), self.hostname)
        layout.addRow(QLabel("PORTA"), self.porta)
        layout.addRow(QLabel("BANCO"), self.banco)
        layout.addRow(QLabel("USUARIO"), self.usuario)
        layout.addRow(QLabel("SENHA"), self.senha)
        layout.addRow(QLabel("COD_VENDEDOR"), self.cod_vendedor)
        layout.addRow(QLabel("COD_PRODUTO_SERVICO"), self.cod_produto_servico)
        layout.addRow(QLabel("COD_PRODUTO_ENTREGA"), self.cod_produto_entrega)
        layout.addRow(QLabel("PAGAMENTO_ENTREGA"), self.pagamento_entrega)
        layout.addRow(QLabel("PAGAMENTO_ONLINE"), self.pagamento_online)
        layout.addRow(QLabel("EMAIL"), self.email)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._load_values()

    def _load_values(self):
        try:
            if not os.path.exists(self.env_path):
                return
            with open(self.env_path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    if "#" in val:
                        val = val.split("#", 1)[0].strip()
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]

                    if key == "DATABASE_URL":
                        try:
                            if val.startswith("sqlserver://"):
                                body = val[len("sqlserver://") :]
                                if ";" in body:
                                    hostport, rest = body.split(";", 1)
                                else:
                                    hostport, rest = body, ""
                                if ":" in hostport:
                                    h, p = hostport.split(":", 1)
                                else:
                                    h, p = hostport, ""
                                self.hostname.setText(h)
                                self.porta.setText(p)
                                parts = rest.split(";") if rest else []
                                for part in parts:
                                    if "=" not in part:
                                        continue
                                    k, v = part.split("=", 1)
                                    k, v = k.strip().lower(), v.strip().strip('"')
                                    if k == "database":
                                        self.banco.setText(v)
                                    elif k == "user":
                                        self.usuario.setText(v)
                                    elif k == "password":
                                        self.senha.setText(v)
                        except Exception:
                            self.hostname.setText(val)
                    elif key == "COD_VENDEDOR":
                        self.cod_vendedor.setText(val)
                    elif key == "COD_PRODUTO_SERVICO":
                        self.cod_produto_servico.setText(val)
                    elif key == "COD_PRODUTO_ENTREGA":
                        self.cod_produto_entrega.setText(val)
                    elif key == "PAGAMENTO_ENTREGA":
                        self.pagamento_entrega.setText(val)
                    elif key == "PAGAMENTO_ONLINE":
                        self.pagamento_online.setText(val)
                    elif key == "EMAIL":
                        self.email.setText(val)
        except Exception as e:
            parent = self.parent()
            if parent is not None:
                QtWidgets.QMessageBox.warning(parent, "Erro", f"Erro ao ler ENV:\n{e}")

    def get_updates(self):
        out = {}
        host = self.hostname.text().strip()
        port = self.porta.text().strip()
        db = self.banco.text().strip()
        user = self.usuario.text().strip()
        pwd = self.senha.text().strip()

        if host:
            hostport = f"{host}:{port}" if port else host
            parts = [f"sqlserver://{hostport}"]
            if db:
                parts.append(f"database={db}")
            if user:
                parts.append(f"user={user}")
            if pwd:
                parts.append(f"password={pwd}")
            parts.append("trustServerCertificate=true")
            composed = ";".join(parts)
            out["DATABASE_URL"] = f'"{composed}"'

        out["COD_VENDEDOR"] = self.cod_vendedor.text() or ""
        out["COD_PRODUTO_SERVICO"] = self.cod_produto_servico.text() or ""
        out["COD_PRODUTO_ENTREGA"] = self.cod_produto_entrega.text() or ""
        out["PAGAMENTO_ENTREGA"] = self.pagamento_entrega.text() or ""
        out["PAGAMENTO_ONLINE"] = self.pagamento_online.text() or "1"
        out["EMAIL"] = self.email.text() or ""
        return out


class GerenciadorServicos(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        if getattr(sys, "frozen", False):
            self.base_dir = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
        else:
            self.base_dir = os.path.dirname(__file__)

        ui_path = os.path.join(self.base_dir, "assets", "apihub.ui")
        uic.loadUi(ui_path, self)

        self.bats = {
            "instalar": r"C:\\INFARMA\\APIHUB\\bats\\1-instala-servicos.bat",
            "excluir": r"C:\\INFARMA\\APIHUB\\bats\\2-exclui-servicos.bat",
        }

        exe_dir = (
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else self.base_dir
        )
        self.env_path = os.path.join(exe_dir, ".env")

        self.create_default_env_if_missing()

        icon_path = os.path.join(self.base_dir, "assets", "apihub-white.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

            # 🎨 ÍCONES DO SISTEMA
        style = self.style()

        # ▶️ Botão Instalar (ícone branco)
        icon = style.standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        pixmap = icon.pixmap(50, 50)

        # Recolorir o ícone em branco
        colored_pixmap = QtGui.QPixmap(pixmap.size())
        colored_pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(colored_pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QtGui.QColor("white"))
        painter.end()

        self.btnInstalar.setIcon(QtGui.QIcon(colored_pixmap))
        self.btnInstalar.setIconSize(QtCore.QSize(50, 50))

        # ▶️ Botão Servico (ícone branco)
        icon = style.standardIcon(QtWidgets.QStyle.SP_MediaStop)
        pixmap = icon.pixmap(50, 50)

        # Recolorir o ícone em branco
        colored_pixmap = QtGui.QPixmap(pixmap.size())
        colored_pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(colored_pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QtGui.QColor("white"))
        painter.end()

        self.btnServico.setIcon(QtGui.QIcon(colored_pixmap))
        self.btnServico.setIconSize(QtCore.QSize(50, 50))

        self.btnInstalar.clicked.connect(self.instalar_servicos)
        self.btnServico.clicked.connect(self.on_btn_servico_click)
        self.btnEditarEnv.clicked.connect(self.on_editar_env)
        self.btnAbrirLog.clicked.connect(self.abrir_log)
        self.btnAbrirDash.clicked.connect(self.abrir_dash)
        self.btnPainel.clicked.connect(self.abrir_painel)

        self.atualizar_status_servico()

    def on_btn_servico_click(self):
        status = self.verificar_status_servico()

        if status == "Não instalado":
            self.instalar_servicos()
        elif status in ("Iniciado", "Não iniciado"):
            self.excluir_servicos()
            self.reset_aplicativo()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Aviso", "Não foi possível determinar o status do serviço."
            )

    def verificar_status_servico(self, nome_servico="vmd-api-hub"):
        try:
            result = subprocess.run(
                ["sc", "query", nome_servico], capture_output=True, text=True
            )
            if "RUNNING" in result.stdout:
                return "Iniciado"
            elif "STOPPED" in result.stdout:
                return "Não iniciado"
            elif "não existe" in result.stdout or "does not exist" in result.stdout:
                return "Não instalado"
            else:
                return "Não iniciado"
        except Exception:
            return "Erro"

    def atualizar_status_servico(self):
        status = self.verificar_status_servico()

        if hasattr(self, "lblStatusServico"):
            self.lblStatusServico.setText(status)

        if hasattr(self, "btnServico"):
            if status == "Iniciado":
                self.lblStatusServico.setStyleSheet("color: green; font-weight: bold;")
                # cor normal = cor de hover; hover = tonalidade mais escura
                self.btnServico.setStyleSheet(
                    """
QPushButton {
    color: rgb(255, 255, 255);
    background-color:   rgb(217, 83,79);   
	font-weight: bold;
   	font-size:80px;
    border-radius: 5px;
    border: none;
    padding: 10px;
}


QPushButton:hover {
    background-color: rgb(150, 57, 54); 
    padding-top: 12px;  /* simula o botão afundando */
}
                """
                )
            elif status == "Não iniciado" or status == "Não instalado":
                self.lblStatusServico.setStyleSheet("color: gray; font-weight: bold;")
                # cinza padrão e hover cinza mais escuro
                self.btnServico.setStyleSheet(
                    """
QPushButton {
    color: rgb(255, 255, 255);
    background-color:   rgb(140, 140, 140); 
	font-weight: bold;
   	font-size:80px;
    border-radius: 5px;
    border: none;
    padding: 10px;
}



QPushButton:hover {
    background-color: rgb(150, 57, 54); 
    padding-top: 12px;  /* simula o botão afundando */
}
                """
                )

        if hasattr(self, "btnInstalar"):
            if status == "Iniciado":
                self.btnInstalar.setStyleSheet(
                    """
                    QPushButton {
    color: rgb(255, 255, 255);
	
	background-color: rgb(0, 197, 0);
    font-weight: bold;
   	font-size:80px;
    border-radius: 5px;
    border: none;
    padding: 10px;
}
 
}
QPushButton:hover{
    
	background-color: rgb(0, 100, 0);
    padding-top: 12px; 
}

                """
                )
            elif status == "Não iniciado" or status == "Não instalado":
                self.btnInstalar.setStyleSheet(
                    """
QPushButton {
    color: rgb(255, 255, 255);
	
	background-color: rgb(140, 140, 140);
    font-weight: bold;
   	font-size:80px;
    border-radius: 5px;
    border: none;
    padding: 10px;
}

 
}
QPushButton:hover{
    
	background-color: rgb(0, 197, 0);
    padding-top: 12px; 
}
                """
                )

    def create_default_env_if_missing(self):
        if os.path.exists(self.env_path):
            return

        default_env = """
        NODE_ENV=production
        PORT=3334
        REDIS_HOST=127.0.0.1
        REDIS_PORT=6379

        TIME_LOG=168

        DATABASE_URL="sqlserver://HOSTNAME:PORTA;database=BANCO;user=USUARIO;password=SENHA;trustServerCertificate=true"
        COD_VENDEDOR=
        COD_PRODUTO_SERVICO=
        COD_PRODUTO_ENTREGA=
        PAGAMENTO_ENTREGA=
        PAGAMENTO_ONLINE=
        EMAIL=

        DIAS_PROCESSA_PEDIDO=5
        DIAS_CANCELA_PEDIDO=0

        NAPP_ORDER_STATUS_FILTER=CONFIRMED

        IFOOD_ORDER_STATUS_FILTER=PLC
        IFOOD_USE_NEW_API=true
        """
        os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write(default_env)

    # ---------- Funções ----------
    def abrir_env(self):
        """Abre o arquivo .env no editor padrão"""
        try:
            os.startfile(self.env_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Não foi possível abrir o arquivo ENV:\n{e}"
            )

    # ---------- .env helpers ----------
    def read_env_preserve(self):
        """Lê o .env retornando linhas e um dicionário de chaves->(value, line_index).
        Preserva comentários e ordem para reescrita."""
        lines = []
        kv = {}
        if not os.path.exists(self.env_path):
            return lines, kv
        with open(self.env_path, "r", encoding="utf-8") as f:
            for idx, raw in enumerate(f.readlines()):
                line = raw.rstrip("\n")
                lines.append(line)
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" in stripped:
                    key, val = stripped.split("=", 1)
                    # remove inline comment for stored value (but keep original line in 'lines')
                    val_part = val.strip()
                    if "#" in val_part:
                        val_no_comment = val_part.split("#", 1)[0].strip()
                    else:
                        val_no_comment = val_part
                    kv[key.strip()] = (val_no_comment, idx)
        return lines, kv

    def write_env_preserve(self, lines, kv_updates):
        """Aplica atualizações (dict key->new_value) nas linhas e escreve no arquivo .env."""
        # atualiza linhas existentes
        for k, v in kv_updates.items():
            # procura na lista de linhas e preserva comentário inline se existir
            found = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith(k + "=") or stripped.split("=")[0].strip() == k:
                    # preserva comentário a partir de '#'
                    comment = ""
                    if "#" in line:
                        idx_hash = line.find("#")
                        comment = line[idx_hash:]
                    lines[i] = f"{k}={v}{comment}"
                    found = True
                    break
            if not found:
                # adiciona ao final sem comentário
                lines.append(f"{k}={v}")

        # escreve no arquivo
        os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
        with open(self.env_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    # ---------- UI handler para editar .env ----------
    def on_editar_env(self):
        try:
            dialog = EnvEditorDialog(self.env_path, self)
            if dialog.exec_() == QDialog.Accepted:
                updates = dialog.get_updates()
                lines, kv = self.read_env_preserve()
                self.write_env_preserve(lines, updates)
                QtWidgets.QMessageBox.information(
                    self, "Sucesso!", "Configurações atualizadas com sucesso!"
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Falha ao abrir configurações:\n{e}"
            )

    def executar_bat(self, caminho_bat):
        """Executa um arquivo .bat e exibe o resultado"""
        try:
            subprocess.run(caminho_bat, check=True, shell=True)
            QtWidgets.QMessageBox.information(
                self, "Sucesso", f"Processo concluído com sucesso."
            )
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Falha ao executar:\n{caminho_bat}\n\n{e}"
            )

    def instalar_servicos(self):
        try:
            self.executar_bat(self.bats["instalar"])
            self.reset_aplicativo()  # 🔄 reinicia depois de instalar
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao instalar serviços:\n{e}"
            )

    def excluir_servicos(self):
        try:
            self.executar_bat(self.bats["excluir"])
            self.reset_aplicativo()  # 🔄 reinicia depois de excluir
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao excluir serviços:\n{e}"
            )

    def abrir_log(self):
        """Abre o arquivo de log no programa padrão do sistema"""
        caminho_log = r"C:\INFARMA\APIHUB\logs\app.log"
        try:
            if os.path.exists(caminho_log):
                os.startfile(caminho_log)
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Erro", f"Arquivo de log não encontrado em:\n{caminho_log}"
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir arquivo de log:\n{e}"
            )

    def abrir_dash(self):
        """Abre o dashboard local no navegador padrão"""
        url_dash = "http://127.0.0.1:3334/dashboard/"
        try:
            webbrowser.open(url_dash)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o dashboard:\n{e}"
            )

    def abrir_painel(self):
        """Abre o Infarma Painel de Pedidos diretamente"""
        localappdata = os.getenv("LOCALAPPDATA")
        #print("LOCALAPPDATA:", localappdata)
        if not localappdata:
            QtWidgets.QMessageBox.warning(self, "Erro", "A variável LOCALAPPDATA não está definida.")
            return

        caminho_painel = os.path.join(
        localappdata,
        "Programs",
        "Infarma Painel de Pedidos",
        "Resources",
        "app.asar.unpacked",
        "config",
        ".env"
    )
       # Programs\Infarma Painel de Pedidos\resources\app.asar.unpacked\config

        try:
            if os.path.exists(caminho_painel):
                os.startfile(caminho_painel)
                
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Erro",
                    f"O ENV do Painel de Pedidos não foi encontrado em:\n{caminho_painel}",
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o ENV Painel de Pedidos:\n{e}"
            )


    def reset_aplicativo(self):
        """Reinicia o estado do aplicativo (como se tivesse acabado de abrir)."""
        try:
            # Atualiza o status do serviço
            self.atualizar_status_servico()

            # Recria o .env padrão se estiver corrompido ou vazio
            if not os.path.exists(self.env_path) or os.path.getsize(self.env_path) == 0:
                self.create_default_env_if_missing()

            # Fecha e reabre a janela (simula reinício completo)
            QtWidgets.QMessageBox.information(
                self,
                "Reiniciando",
                "O aplicativo será reiniciado para aplicar as alterações.",
            )
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Falha Catastrófica:\n{e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GerenciadorServicos()
    window.show()
    sys.exit(app.exec_())
