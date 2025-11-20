import sys
import os
import webbrowser
import subprocess
from assets.apihub_ui import Ui_GerenciadorServicos
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
import pyodbc
from PyQt5.QtWidgets import QGridLayout , QHBoxLayout,QMessageBox


class EnvEditorDialog(QDialog):
    
    def __init__(self, env_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar configurações")
        self.env_path = env_path

        try:
            # Largura/Altura da janela
            self.setMinimumWidth(600)
            self.setMaximumWidth(600)
            self.setMaximumHeight(300)
            self.setMinimumHeight(300)
        except Exception:
            pass

        # 1. Crie o layout principal (QGridLayout)
        layout = QGridLayout(self)

        # 2. Crie todos os widgets ANTES de adicioná-los ao layout
        # DADOS DE CONEXÃO
        self.hostname = QLineEdit()
        self.porta = QLineEdit()
        self.banco = QLineEdit()
        self.usuario = QLineEdit()
        self.senha = QLineEdit()

        # CÓDIGOS E PAGAMENTOS
        self.cod_vendedor = QLineEdit()
        self.cod_produto_servico = QLineEdit()
        self.cod_produto_entrega = QLineEdit()
        self.pagamento_entrega = QLineEdit()
        self.pagamento_online = QLineEdit()
        self.email = QLineEdit() 

        # ------------------------------------------------------------------
        # ORGANIZAÇÃO EM GRADE (4 COLUNAS) - O seu código existente
        # ------------------------------------------------------------------

        linha = 0
        # Linha 0
        layout.addWidget(QLabel("HOSTNAME"), linha, 0)
        layout.addWidget(self.hostname, linha, 1)
        layout.addWidget(QLabel("COD_VENDEDOR"), linha, 2)
        layout.addWidget(self.cod_vendedor, linha, 3)

        linha += 1
        # Linha 1
        layout.addWidget(QLabel("PORTA"), linha, 0)
        layout.addWidget(self.porta, linha, 1)
        layout.addWidget(QLabel("COD_PRODUTO_SERVICO"), linha, 2)
        layout.addWidget(self.cod_produto_servico, linha, 3)

        linha += 1
        # Linha 2
        layout.addWidget(QLabel("BANCO"), linha, 0)
        layout.addWidget(self.banco, linha, 1)
        layout.addWidget(QLabel("COD_PRODUTO_ENTREGA"), linha, 2)
        layout.addWidget(self.cod_produto_entrega, linha, 3)

        linha += 1
        # Linha 3
        layout.addWidget(QLabel("USUARIO"), linha, 0)
        layout.addWidget(self.usuario, linha, 1)
        layout.addWidget(QLabel("PAGAMENTO_ENTREGA"), linha, 2)
        layout.addWidget(self.pagamento_entrega, linha, 3)

        linha += 1
        # Linha 4
        layout.addWidget(QLabel("SENHA"), linha, 0)
        layout.addWidget(self.senha, linha, 1)
        layout.addWidget(QLabel("PAGAMENTO_ONLINE"), linha, 2)
        layout.addWidget(self.pagamento_online, linha, 3)

        # ------------------------------------------------------------------
        # CAMPO EMAIL (Ocupando as 4 colunas no final)
        # ------------------------------------------------------------------

        linha += 1
        # Rótulo na Coluna 0
        layout.addWidget(QLabel("EMAIL"), linha, 0)
        # Campo de Texto se estendendo por 3 colunas (1, 2, 3)
        layout.addWidget(self.email, linha, 1, 1, 3)

        # ------------------------------------------------------------------
        # DICAS DE LAYOUT
        # ------------------------------------------------------------------
        # Faz com que as colunas dos campos (1 e 3) ocupem o espaço disponível
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.setStyleSheet("""
        QLineEdit {
            border-radius: 5px; /* Arredondamento */
            padding: 5px;
            border: 1px solid #cccccc; /* Para que a borda arredondada seja visível */
        }
        """)



        # QDialogButtonBox (Contém OK/Salvar e Cancel/Sair)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok ) 
                                   #QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        buttons.setCenterButtons(True)  # CENTRALIZA DENTRO DO BUTTONBOX

        ok_button = buttons.button(QDialogButtonBox.Ok)

        if ok_button:
            ok_button.setText("Salvar")
            ok_button.setFixedSize(500, 35)  # tamanho que você colocou
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45A049;
                }
                QPushButton:pressed {
                    background-color: #3E8E41;
                }
            """)



        # NOVO: Crie um Layout Horizontal para a linha dos botões
        botoes_layout = QtWidgets.QHBoxLayout()

        # 3. Adicione o QDialogButtonBox (Salvar e Sair)
        botoes_layout.addWidget(buttons)

        # 4. Adicione o QHBoxLayout na linha final do QGridLayout
        linha += 1
        # Linha, Coluna, Linhas a Abranger, Colunas a Abranger
        layout.addLayout(botoes_layout, linha, 0, 1, 4)


        self._load_values()
        
        
    def validate_and_save(self):
        # 1. Obter dados do formulário
        host = self.hostname.text().strip()
        port = self.porta.text().strip()
        db = self.banco.text().strip()
        user = self.usuario.text().strip()
        pwd = self.senha.text().strip()

        cod_vendedor = self.cod_vendedor.text().strip()
        cod_produto_servico = self.cod_produto_servico.text().strip()
        cod_produto_entrega = self.cod_produto_entrega.text().strip()
        pagamento_entrega = self.pagamento_entrega.text().strip()
        pagamento_online = self.pagamento_online.text().strip()

        # 2. Verificar se os campos de conexão estão preenchidos
        if not (host and db and user and pwd):
            QMessageBox.warning(
                self, "Erro de Validação", "Preencha todos os campos de conexão (HOSTNAME, BANCO, USUARIO, SENHA) antes de salvar."
            )
            return False

        # 3. Verificar se todos os campos de código estão preenchidos
        if not (cod_vendedor and cod_produto_servico and cod_produto_entrega and pagamento_entrega and pagamento_online):
            QMessageBox.warning(
                self, "Erro de Validação", "Preencha todos os códigos (Vendedor, Produtos e Pagamentos)."
            )
            return False
        
        conn = None
        cursor = None
        try:
            # Tenta estabelecer a conexão
            hostport = f"{host},{port}" if port else host
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={hostport};DATABASE={db};UID={user};PWD={pwd};TrustServerCertificate=yes"
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()

            # Estrutura de validação (Código, Tabela, Coluna, Mensagem de Erro)
            validations = [
                (cod_vendedor, "VENDE", "COD_VENDED", f"Vendedor (COD_VENDEDOR={cod_vendedor})"),
                (cod_produto_servico, "PRODU", "COD_PRODUT", f"Produto Serviço (COD_PRODUTO_SERVICO={cod_produto_servico})"),
                (cod_produto_entrega, "PRODU", "COD_PRODUT", f"Produto Entrega (COD_PRODUTO_ENTREGA={cod_produto_entrega})"),
                (pagamento_entrega, "FPGCB", "COD_FORPAG", f"Pagamento Entrega (PAGAMENTO_ENTREGA={pagamento_entrega})"),
                (pagamento_online, "FPGCB", "COD_FORPAG", f"Pagamento Online (PAGAMENTO_ONLINE={pagamento_online})"),
            ]
            
            # Executa as validações
            for value, table, column, error_msg in validations:
                # Usa COUNT para verificar a existência de forma eficiente
                query = f"SELECT COUNT(*) FROM {table} WHERE {column} = ?"
                cursor.execute(query, value)
                count = cursor.fetchone()[0]

                if count == 0:
                    QMessageBox.warning(
                        self, "Erro de Validação", f"O código não foi encontrado no banco de dados:\n\n- {error_msg}"
                    )
                    return False # Falhou na validação

            # Se chegou até aqui, todas as validações de código passaram
            return True

        except pyodbc.Error as e:
            QMessageBox.critical(
                self, "Erro de Conexão/SQL", f"Falha durante a validação no banco de dados. Verifique os dados de conexão ou as permissões:\n\n{e}"
            )
            return False # Falhou devido a erro de conexão/SQL
        except Exception as e:
            QMessageBox.critical(
                self, "Erro Desconhecido", f"Ocorreu um erro inesperado durante a validação:\n\n{e}"
            )
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Sobrescrever o método accept
    def accept(self):
        """
        Sobrescreve o método accept (chamado pelo botão Salvar) para incluir a validação
        antes de realmente aceitar e fechar o diálogo.
        """
        if self.validate_and_save():
            # Chama o método original da classe base se a validação for bem-sucedida
            super().accept()
        
    def testar_conexao(self):
        host = self.hostname.text().strip()
        port = self.porta.text().strip()
        db = self.banco.text().strip()
        user = self.usuario.text().strip()
        pwd = self.senha.text().strip()
        

        if not host or not db or not pwd or not user:
            QtWidgets.QMessageBox.warning(
                self, "Erro", "Por favor, preencha os dados para testar a conexão."
            )
            return

        try:
            hostport = f"{host},{port}" if port else host
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={hostport};DATABASE={db};UID={user};PWD={pwd};TrustServerCertificate=yes"
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Conexão bem-sucedida!")
        except Exception as e:
            #QtWidgets.QMessageBox.warning(self, "Erro", f"Falha na conexão:\n{e}")
            QtWidgets.QMessageBox.warning(self, "Erro", f"Erro na conexão! Verifique os dados informados e tente novamente.")  

    def _load_values(self):
        try:
            if not os.path.exists(self.env_path):
                print("Passou aqui")
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
                                    hostport, rest = body.split(";",1)
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
        out["PAGAMENTO_ONLINE"] = self.pagamento_online.text() or ""
        out["EMAIL"] = self.email.text() or ""
        return out


class GerenciadorServicos(QtWidgets.QMainWindow,Ui_GerenciadorServicos):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        if getattr(sys, "frozen", False):
            self.base_dir = sys._MEIPASS  # Caminho temporário do PyInstaller
        else:
            self.base_dir = os.path.dirname(__file__)


        self.bats = {
            "instalar": r"C:\\INFARMA\\APIHUB\\bats\\1-instala-servicos.bat",
            "excluir": r"C:\\INFARMA\\APIHUB\\bats\\2-exclui-servicos.bat",
        }

        exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else self.base_dir
        
        for key, path in self.bats.items():
            if not os.path.exists(path):
                print(f"Aviso: arquivo BAT não encontrado -> {path}")
               

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
        self.btnLogErr.clicked.connect(self.abrir_painel_log_error)
        self.btnLogAll.clicked.connect(self.abrir_painel_log_all)

        self.atualizar_status_servico()

    def on_btn_servico_click(self):
        status = self.verificar_status_servico()

        if status == "Não instalado":
            self.instalar_servicos()
        elif status in ("Iniciado", "Não iniciado"):
            self.excluir_servicos()
            #self.reset_aplicativo()
            self.atualizar_status_servico()
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

        default_env = """NODE_ENV=production
PORT=3334
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Tempo para persistir o LOG em horas | default 7 * 24 = 168
TIME_LOG=168

# BANCO DE DADOS PARA ACESSO
DATABASE_URL="sqlserver://HOSTNAME:PORTA;database=BANCO;user=USUARIO;password=SENHA;trustServerCertificate=true"
COD_VENDEDOR= #VENDEDOR PADRÃO PARA RECEBER OS PEDIDOS
COD_PRODUTO_SERVICO= #PRODUTOS TIPO SERVIÇO PARA INCLUSÃO DE TAXAS
COD_PRODUTO_ENTREGA= #PRODUTOS TIPO ENTREGA PARA INCLUSÃO DE TAXA DE ENTREGA
PAGAMENTO_ENTREGA= #FORMA DE PAGAMENTO PARA ENTREGA / PAGAR NA ENTREGA
PAGAMENTO_ONLINE= #FORMA DE PAGAMENTO PARA ONLINE / PAGAMENTO NA PLATAFORMA
EMAIL= #EMAIL PARA ENVIO DE NOTIFICAÇÕES

# Dias para consulta de pedidos FastApp
DIAS_PROCESSA_PEDIDO=5
DIAS_CANCELA_PEDIDO=0

NAPP_ORDER_STATUS_FILTER=CONFIRMED #STATUS DO PEDIDO PARA CONSULTA NAPP

IFOOD_ORDER_STATUS_FILTER=PLC #STATUS DO PEDIDO PARA CONSULTA IFOOD
IFOOD_USE_NEW_API=true 
        """
        os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write(default_env)

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
            #self.reset_aplicativo()  # 🔄 reinicia depois de instalar
            self.atualizar_status_servico()
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao instalar serviços:\n{e}"
            )

    def excluir_servicos(self):
        try:
            self.executar_bat(self.bats["excluir"])
            #self.reset_aplicativo()  # 🔄 reinicia depois de excluir
            self.atualizar_status_servico()
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

    def abrir_painel_log_error(self):
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
        "logs"
        "error.log"
    )
       # Programs\Infarma Painel de Pedidos\resources\app.asar.unpacked\config

        try:
            if os.path.exists(caminho_painel):
                os.startfile(caminho_painel)
                
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Erro",
                    f"O LOG do Painel de Pedidos não foi encontrado em:\n{caminho_painel}",
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o LOG Painel de Pedidos:\n{e}"
            )
            
    def abrir_painel_log_all(self):
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
        "logs",
        "all.log"
    )
       # Programs\Infarma Painel de Pedidos\resources\app.asar.unpacked\config

        try:
            if os.path.exists(caminho_painel):
                os.startfile(caminho_painel)
                
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Erro",
                    f"O LOG do Painel de Pedidos não foi encontrado em:\n{caminho_painel}",
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o LOG Painel de Pedidos:\n{e}"
            )
            
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GerenciadorServicos()
    window.show()
    sys.exit(app.exec_())
