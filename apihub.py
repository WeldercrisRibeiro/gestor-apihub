import sys
import os
import subprocess
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel


class EnvEditorDialog(QDialog):
    """Diálogo simples para editar as chaves do .env solicitadas pelo usuário.

    Exibe campos separados para HOSTNAME, PORTA, BANCO, USUARIO, SENHA em vez de um
    único campo DATABASE_URL. Também mostra os outros campos existentes.
    """

    def __init__(self, env_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Editar configurações')
        self.env_path = env_path

        # ajustar tamanho inicial - deixar a janela um pouco mais larga
        # altere o primeiro valor (largura) para aumentar/diminuir conforme desejado
        try:
            self.resize(100, 200)
            # define largura mínima para evitar que os campos fiquem muito comprimidos
            self.setMinimumWidth(300)
        except Exception:
            # em situações raras (diferentes backends) ignore
            pass

        layout = QFormLayout(self)

        # campos separados para DATABASE_URL
        self.hostname = QLineEdit()
        self.porta = QLineEdit()
        self.banco = QLineEdit()
        self.usuario = QLineEdit()
        self.senha = QLineEdit()

        # outros campos
        self.cod_vendedor = QLineEdit()
        self.cod_servico = QLineEdit()
        self.pagamento_entrega = QLineEdit()
        self.pagamento_online = QLineEdit()
        self.email = QLineEdit()

        layout.addRow(QLabel('HOSTNAME'), self.hostname)
        layout.addRow(QLabel('PORTA'), self.porta)
        layout.addRow(QLabel('BANCO'), self.banco)
        layout.addRow(QLabel('USUARIO'), self.usuario)
        layout.addRow(QLabel('SENHA'), self.senha)

        layout.addRow(QLabel('COD_VENDEDOR'), self.cod_vendedor)
        layout.addRow(QLabel('COD_SERVICO'), self.cod_servico)
        layout.addRow(QLabel('PAGAMENTO_ENTREGA'), self.pagamento_entrega)
        layout.addRow(QLabel('PAGAMENTO_ONLINE'), self.pagamento_online)
        layout.addRow(QLabel('EMAIL'), self.email)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        # preenche com valores atuais se existir
        self._load_values()

    def _load_values(self):
        try:
            if not os.path.exists(self.env_path):
                return
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    # remove inline comment (apenas para exibição)
                    if '#' in val:
                        val = val.split('#', 1)[0].strip()
                    # remove aspas se houver
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]

                    if key == 'DATABASE_URL':
                        # parseia o formato esperado: sqlserver://HOST:PORT;database=DB;user=USER;password=PWD;...
                        try:
                            parsed = val
                            if parsed.startswith('sqlserver://'):
                                body = parsed[len('sqlserver://'):]
                                # separa HOST:PORT do resto
                                if ';' in body:
                                    hostport, rest = body.split(';', 1)
                                else:
                                    hostport, rest = body, ''
                                if ':' in hostport:
                                    h, p = hostport.split(':', 1)
                                else:
                                    h, p = hostport, ''
                                self.hostname.setText(h)
                                self.porta.setText(p)
                                # parsea rest como key=val;...
                                parts = rest.split(';') if rest else []
                                for part in parts:
                                    if '=' not in part:
                                        continue
                                    k, v = part.split('=', 1)
                                    k = k.strip().lower()
                                    v = v.strip().strip('"')
                                    if k == 'database':
                                        self.banco.setText(v)
                                    elif k == 'user':
                                        self.usuario.setText(v)
                                    elif k == 'password':
                                        self.senha.setText(v)
                        except Exception:
                            # falha no parse: coloca tudo em HOSTNAME para não perder informação
                            self.hostname.setText(val)
                    elif key == 'COD_VENDEDOR':
                        self.cod_vendedor.setText(val)
                    elif key == 'COD_SERVICO':
                        self.cod_servico.setText(val)
                    elif key == 'PAGAMENTO_ENTREGA':
                        self.pagamento_entrega.setText(val)
                    elif key == 'PAGAMENTO_ONLINE':
                        self.pagamento_online.setText(val)
                    elif key == 'EMAIL':
                        self.email.setText(val)
        except Exception as e:
            try:
                parent = self.parent()
                if parent is not None:
                    QtWidgets.QMessageBox.warning(parent, 'Erro', f'Erro ao ler ENV:\n{e}')
            except Exception:
                pass

    def get_updates(self):
        out = {}
        # compõe DATABASE_URL a partir dos campos separados
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
            # garante trustServerCertificate para compatibilidade
            parts.append('trustServerCertificate=true')
            composed = ';'.join(parts)
            # envolver em aspas para preservar ; no value
            out['DATABASE_URL'] = f'"{composed}"'

        out['COD_VENDEDOR'] = self.cod_vendedor.text() or '1'
        out['COD_SERVICO'] = self.cod_servico.text() or '1'
        out['PAGAMENTO_ENTREGA'] = self.pagamento_entrega.text() or '1'
        out['PAGAMENTO_ONLINE'] = self.pagamento_online.text() or '1'
        out['EMAIL'] = self.email.text() or ''
        return out


class GerenciadorServicos(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Caminho base: quando empacotado com PyInstaller os recursos ficam em
        # sys._MEIPASS. Caso contrário usa o diretório do arquivo.
        if getattr(sys, 'frozen', False):
            # runtime path set by PyInstaller
            self.base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
        else:
            self.base_dir = os.path.dirname(__file__)

        # Carrega o arquivo .ui a partir de assets (suporta execução empacotada)
        ui_path = os.path.join(self.base_dir, "assets", "apihub.ui")
        if not os.path.exists(ui_path):
            # fallback para desenvolvimento (caso esteja executando de outro cwd)
            ui_path = os.path.join(os.path.dirname(__file__), "assets", "apihub.ui")
        uic.loadUi(ui_path, self)

        # Caminhos dos arquivos BAT
        self.bats = {
            "instalar": r"C:\\INFARMA\\APIHUB\\bats\\1-instala-servicos.bat",
            
            "excluir": r"C:\\INFARMA\\APIHUB\\bats\\2-exclui-servicos.bat"
           
        }

        # Caminho do arquivo .env (usa pasta do executável quando empacotado)
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else self.base_dir
        self.env_path = os.path.join(exe_dir, ".env")

        # Ícone do app
        # carrega ícone a partir dos assets empacotados ou do diretório de origem
        icon_path = os.path.join(self.base_dir, "assets", "apihub-white.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "apihub-white.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Conecta os botões (uso try/except para compatibilidade com variações de UI)
        try:
            self.btnInstalar.clicked.connect(self.instalar_servicos)
        except Exception:
            pass

        try:
            self.btnExcluir.clicked.connect(self.excluir_servicos)
        except Exception:
            pass

        try:
            self.btnEditarEnv.clicked.connect(self.on_editar_env)
        except Exception:
            pass

        try:
            self.btnAbrirLog.clicked.connect(self.abrir_log)
        except Exception:
            pass

    # ---------- Funções ----------
    def abrir_env(self):
        """Abre o arquivo .env no editor padrão"""
        try:
            os.startfile(self.env_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo ENV:\n{e}")

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
                line = raw.rstrip('\n')
                lines.append(line)
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if '=' in stripped:
                    key, val = stripped.split('=', 1)
                    # remove inline comment for stored value (but keep original line in 'lines')
                    val_part = val.strip()
                    if '#' in val_part:
                        val_no_comment = val_part.split('#', 1)[0].strip()
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
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped.startswith(k + "=") or stripped.split('=')[0].strip() == k:
                    # preserva comentário a partir de '#'
                    comment = ''
                    if '#' in line:
                        idx_hash = line.find('#')
                        comment = line[idx_hash:]
                    lines[i] = f"{k}={v}{comment}"
                    found = True
                    break
            if not found:
                # adiciona ao final sem comentário
                lines.append(f"{k}={v}")

        # escreve no arquivo
        os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
        with open(self.env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')

    # ---------- UI handler para editar .env ----------
    def on_editar_env(self):
        try:
            dialog = EnvEditorDialog(self.env_path, self)
            if dialog.exec_() == QDialog.Accepted:
                updates = dialog.get_updates()
                lines, kv = self.read_env_preserve()
                self.write_env_preserve(lines, updates)
                QtWidgets.QMessageBox.information(self, 'Sucesso!', 'Configurações atualizadas com sucesso!')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Erro', f'Falha ao abrir configurações:\n{e}')

    def executar_bat(self, caminho_bat):
        """Executa um arquivo .bat e exibe o resultado"""
        try:
            subprocess.run(caminho_bat, check=True, shell=True)
            QtWidgets.QMessageBox.information(self, "Sucesso", f"Processo concluído com sucesso.")
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Falha ao executar:\n{caminho_bat}\n\n{e}")

    def instalar_servicos(self):
        try:
            self.executar_bat(self.bats["instalar"])
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Erro', f'Erro ao instalar serviços:\n{e}')


    def excluir_servicos(self):
        try:
            self.executar_bat(self.bats["excluir"])
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Erro', f'Erro ao excluir serviços:\n{e}')

    def abrir_log(self):
        """Abre o arquivo de log no programa padrão do sistema"""
        caminho_log = r"C:\INFARMA\APIHUB\logs\app.log"
        try:
            if os.path.exists(caminho_log):
                os.startfile(caminho_log)
            else:
                QtWidgets.QMessageBox.warning(self, 'Erro', f'Arquivo de log não encontrado em:\n{caminho_log}')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Erro', f'Erro ao abrir arquivo de log:\n{e}')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GerenciadorServicos()
    window.show()
    sys.exit(app.exec_())
