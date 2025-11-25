import sys
import os
import webbrowser
import subprocess
import platform
import time
import requests 
import pyodbc
import qtawesome as qta 

from assets.apihub_ui import Ui_GerenciadorServicos
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QDialog, QLineEdit, QDialogButtonBox, QLabel, QGridLayout, QMessageBox, QListWidget, QListWidgetItem, QPushButton) # ADICIONADO QListWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo




class Config:
    SERVICE_NAME_API = "vmd-api-hub"
    SERVICE_NAME_REDIS = "redis-service"
    BASE_DIR_INFARMA = r"C:\INFARMA\APIHUB"
    LOG_PATH_API = os.path.join(BASE_DIR_INFARMA, "logs", "app.log")
    URL_DASHBOARD = "http://127.0.0.1:3334/dashboard/"
    

    REPO_FULL_NAME = "WeldercrisRibeiro/infarma-apihub" 
    TARGET_FILE_NAME = "vmd-api-hub.exe"
   
    @staticmethod
    def get_painel_base_path():
        localappdata = os.getenv("LOCALAPPDATA")
        if not localappdata:
            return None
        return os.path.join(localappdata, "Programs", "Infarma Painel de Pedidos")

    @staticmethod
    def get_painel_env_path():
        base = Config.get_painel_base_path()
        return os.path.join(base, "resources", "app.asar.unpacked", "config", ".env") if base else None
    
    @staticmethod
    def get_painel_log_all_path():
        base = Config.get_painel_base_path()
        return os.path.join(base, "logs", "all.log") if base else None



def get_available_versions(repo_name: str) -> list:
    """Consulta a API do GitHub para obter as releases e extrair a versão e o link do executável."""
    API_URL = f"https://api.github.com/repos/{repo_name}/releases"
    
    try:
        # 1. Faz a requisição para a API de Releases do GitHub
        response = requests.get(API_URL)
        response.raise_for_status() # Lança exceção para códigos de erro HTTP
        releases_data = response.json()
        
        versions = []
        
        # 2. Itera sobre cada release e busca o executável
        for release in releases_data:
            version_tag = release.get("tag_name")
            download_url = None
            
            # As 'assets' são os arquivos anexados à release (seu EXE)
            for asset in release.get("assets", []):
                # Assumimos que o nome do asset é o nome do executável
                if asset.get("name") == Config.TARGET_FILE_NAME:
                    # Usamos 'browser_download_url' para o download direto
                    download_url = asset.get("browser_download_url")
                    break
            
            # Ignora drafts e releases sem o executável correto
            if version_tag and download_url and not release.get("draft"):
                versions.append({
                    "version": version_tag,
                    "download_url": download_url
                })
        
        return versions
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com o GitHub: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado na listagem de releases: {e}")
        return []



class DownloadWorker(QThread):
    """Worker que executa o download em uma thread separada."""
    # Sinal emitido ao progresso
    progress_signal = pyqtSignal(int) 
    # Sinal emitido ao fim (True=Sucesso/False=Falha, Message=String)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, download_url: str, target_filename: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_filename = target_filename

    def run(self):
        full_target_path = os.path.join(Config.BASE_DIR_INFARMA, self.target_filename)
        
        if not os.path.isdir(Config.BASE_DIR_INFARMA):
            self.finished_signal.emit(False, f"Diretório de destino não existe: {Config.BASE_DIR_INFARMA}")
            return
        
        # ⚠️ TENTA PARAR O SERVIÇO ANTES DE SUBSTITUIR O EXECUTÁVEL
        try:
             subprocess.run(["net", "stop", Config.SERVICE_NAME_API], creationflags=subprocess.CREATE_NO_WINDOW)
             time.sleep(2) # Pequena pausa para garantir que o serviço pare.
             # Para o REDIS também, caso ele esteja relacionado:
             subprocess.run(["net", "stop", Config.SERVICE_NAME_REDIS], creationflags=subprocess.CREATE_NO_WINDOW)
             time.sleep(1)
        except Exception:
             pass 

        try:
            with requests.get(self.download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with open(full_target_path, 'wb') as f:
                    downloaded_size = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = int((downloaded_size / total_size) * 100)
                                self.progress_signal.emit(progress)

            self.finished_signal.emit(True, f"Apihub atualizado com sucesso!")

            

        except requests.exceptions.RequestException as e:
            self.finished_signal.emit(False, f"Erro durante o download do arquivo:\n{e}")
        except IOError as e:
            # ERRO MAIS COMUM: O EXE ESTÁ EM USO
            self.finished_signal.emit(False, f"Erro ao salvar o arquivo no disco (IOError). O '{Config.SERVICE_NAME_API}' provavelmente está em uso. Por favor, **pare o serviço manualmente** antes de tentar a atualização.")
        except Exception as e:
            self.finished_signal.emit(False, f"Ocorreu um erro inesperado: {e}")

class VersionsDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualização Apihub")
        self.setFixedSize(400, 350)
        self.thread = None 

        
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e; /* Fundo cinza escuro */
                color: #ffffff; /* Texto principal branco */
            }
            QLabel {
                color: #ffffff; /* Labels em branco */
                padding: 5px 0;
            }
            QListWidget {
                background-color: #1e1e1e; /* Fundo da lista mais escuro */
                border: 1px solid #444444; /* Borda sutil */
                color: #ffffff;
                selection-background-color: #005090; /* Azul escuro para seleção */
                selection-color: #ffffff;
            }
            QPushButton {
                background-color: #000000; /* Botões pretos */
                color: #ffffff;
                font-weight: bold;
                border-radius: 5px;
                border: none;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #005090; /* Hover azul escuro, como nos botões secundários da tela principal */
            }
            QPushButton#btn_download { /* Estilo específico para o botão de Baixar */
                background-color: #4CAF50; /* Verde, para ação primária (se quiser manter o padrão de sucesso) */
            }
            QPushButton#btn_download:hover {
                background-color: #45A049;
            }
            QPushButton#btn_download:pressed {
                background-color: #3E8E41;
            }
            QPushButton#btn_close { /* Estilo específico para o botão Fechar */
                background-color: #C82333; /* Vermelho, como o Desinstalar */
            }
            QPushButton#btn_close:hover {
                background-color: #e02b3c;
            }
            
        """)
        # --- FIM DO BLOCO DE ESTILIZAÇÃO ---

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # 1. Label de Instrução
        label = QtWidgets.QLabel("Selecione a versão desejada e clique em Baixar:")
        layout.addWidget(label)

        # 2. QListWidget para Versões
        self.listWidget_versions = QListWidget()
        layout.addWidget(self.listWidget_versions)

        # 3. Botão Baixar
        self.btn_download = QPushButton("Baixar e Substituir")
        self.btn_download.setObjectName("btn_download") # Necessário para o estilo
        self.btn_download.setEnabled(False) 
        self.btn_download.clicked.connect(self.start_update)
        layout.addWidget(self.btn_download)

        # 4. Label de Status do Download
        self.lbl_status_download = QLabel("Status: Aguardando seleção...")
        layout.addWidget(self.lbl_status_download)
        
        # 5. Adicionar um botão de Fechar (opcional, mas bom para UX)
        self.btn_close = QPushButton("Fechar")
        self.btn_close.setObjectName("btn_close") # Necessário para o estilo
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)

        # Conexão: Habilitar o botão de download ao selecionar um item
        self.listWidget_versions.itemSelectionChanged.connect(self.enable_download_button)

        # Carregar as versões na inicialização
        self.load_versions()
    
    def enable_download_button(self):
        """Habilita o botão Baixar se um item estiver selecionado."""
        self.btn_download.setEnabled(bool(self.listWidget_versions.selectedItems()))

    def load_versions(self):
        """Busca as versões do GitHub e popula o QListWidget."""
        self.listWidget_versions.addItem(QListWidgetItem("Carregando versões..."))
        QtWidgets.QApplication.processEvents()
        
        versions = get_available_versions(Config.REPO_FULL_NAME)
        self.listWidget_versions.clear()

        if not versions:
            QMessageBox.warning(self, "Aviso", f"Não foi possível carregar as releases do repositório {Config.REPO_FULL_NAME}. Verifique a conexão.")
            return
        
        for v_info in versions:
            item = QListWidgetItem(v_info["version"])
            # Armazenamos o URL de download como 'data' no item (Role: 1)
            item.setData(1, v_info["download_url"]) 
            self.listWidget_versions.addItem(item)

    def start_update(self):
        """Prepara e inicia a thread de download, validando se uma versão foi selecionada."""
        
        selected_items = self.listWidget_versions.selectedItems()
        
        # -------------------------------------------------------------
        # --- VALIDAÇÃO DE SELEÇÃO (Funcionalidade) ---
        # -------------------------------------------------------------
        # Se a lista de itens selecionados estiver vazia, exibe o aviso.
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma versão da lista antes de clicar em Baixar e Substituir.")
            return # IMPEDE a execução do restante do método.
        # -------------------------------------------------------------
        
        # O código só continua se selected_items tiver pelo menos um item.
        item = selected_items[0]
        version = item.text()
        download_url = item.data(1)
        
        if not download_url:
            QMessageBox.critical(self, "Erro", "URL de download não encontrada.")
            return
            
        first_reply_msg = QMessageBox(self)
        first_reply_msg.setStyleSheet(self.styleSheet()) 
        first_reply_msg.setWindowTitle('Confirmação de Versão')
        first_reply_msg.setText(f"Você selecionou a versão {version}.\n\nDeseja continuar?")
        first_reply_msg.setIcon(QMessageBox.Question)
        
        # Adiciona botões customizados com o texto em Português
        btn_sim_v1 = first_reply_msg.addButton("SIM", QMessageBox.YesRole)
        btn_nao_v1 = first_reply_msg.addButton("NÃO", QMessageBox.NoRole)
        
        # Executa o primeiro diálogo
        first_reply_msg.exec_()
        
        # Verifica o resultado do primeiro diálogo
        if first_reply_msg.clickedButton() == btn_nao_v1:
            return
            
        # -------------------------------------------------------------
        # --- 2. CONFIRMAÇÃO FINAL DE SUBSTITUIÇÃO ---
        # -------------------------------------------------------------
            
        # Segundo, confirma a ação de substituição
        final_msg = QMessageBox(self)
        final_msg.setStyleSheet(self.styleSheet()) 
        final_msg.setWindowTitle('⚠️ Confirmação Final de Atualização')
        final_msg.setText(f"Após confirmar, o executável vmd-api-hub será substituído pela versão {version}. Você tem certeza disso?")
        final_msg.setIcon(QMessageBox.Warning)
        
        # Adiciona botões customizados com o texto em Português
        btn_sim = final_msg.addButton("SIM", QMessageBox.YesRole)
        btn_nao = final_msg.addButton("NÃO", QMessageBox.NoRole)
        
        # Executa a caixa de diálogo
        final_msg.exec_()
        
        # Verifica qual botão foi clicado
        if final_msg.clickedButton() == btn_sim:
            
            # Feedback visual e desabilita botões
            self.btn_download.setEnabled(False)
            self.listWidget_versions.setEnabled(False)
            self.lbl_status_download.setText(f"Status: Iniciando download do vmd-api-hub-{version}...")
            
            # Cria e inicia a Thread
            self.thread = DownloadWorker(download_url, Config.TARGET_FILE_NAME, self)
            self.thread.progress_signal.connect(self.update_download_status)
            self.thread.finished_signal.connect(self.download_finished)
            self.thread.start()
        
    def update_download_status(self, progress: int):
        """Atualiza o label de status com o progresso (em porcentagem)."""
        self.lbl_status_download.setText(f"Status: Baixando... {progress}% concluído")

    def download_finished(self, success: bool, message: str):
        """Trata o resultado da thread de download."""
        self.btn_download.setEnabled(True) # Reabilita o botão
        self.listWidget_versions.setEnabled(True)
        self.lbl_status_download.setText("Status: Concluído.")
        
        if success:
            QMessageBox.information(
                self, "Sucesso!", f"Atualização finalizada:\n\n{message}"
            )

            
            # Atualiza o status do serviço na janela principal
            if self.parent() and hasattr(self.parent(), 'atualizar_status_servico'):
                self.parent().atualizar_status_servico()

            self.accept()
        else:
            QMessageBox.critical(
                self, "Falha na Atualização", message
            )
            

class DatabaseValidator:
    def __init__(self, host, port, db, user, pwd):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.pwd = pwd

    def check_connection_and_codes(self, cod_vendedor, cod_produto_servico, cod_produto_entrega, pagamento_entrega, pagamento_online):
        
        # 1. Verificar se os campos de conexão estão preenchidos
        if not (self.host and self.db and self.user and self.pwd):
            return False, "Preencha todos os campos de conexão (HOSTNAME, BANCO, USUARIO, SENHA) antes de salvar."

        # 2. Verificar se todos os campos de código estão preenchidos
        if not (cod_vendedor and cod_produto_servico and cod_produto_entrega and pagamento_entrega and pagamento_online):
            return False, "Preencha todos os códigos (Vendedor, Produtos e Pagamentos)."
        
        conn = None
        cursor = None
        try:
            # Tenta estabelecer a conexão
            hostport = f"{self.host},{self.port}" if self.port else self.host
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={hostport};DATABASE={self.db};UID={self.user};PWD={self.pwd};TrustServerCertificate=yes"
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
                query = f"SELECT COUNT(*) FROM {table} WHERE {column} = ?"
                cursor.execute(query, value)
                count = cursor.fetchone()[0]

                if count == 0:
                    return False, f"O código não foi encontrado no banco de dados:\n\n- {error_msg}" 

            # Se chegou até aqui, todas as validações passaram
            return True, None

        except pyodbc.Error as e:
            return False, f"Falha durante a validação no banco de dados. Verifique os dados de conexão ou as permissões:\n\n{e}"
        except Exception as e:
            return False, f"Ocorreu um erro inesperado durante a validação:\n\n{e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

class EnvEditorDialog(QDialog):
    
    def __init__(self, env_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar configurações")
        self.env_path = env_path

        try:
            self.setFixedSize(600, 300)
        except Exception:
            pass

        # 1. Crie o layout principal (QGridLayout)
        layout = QGridLayout(self)

        # 2. Crie todos os widgets ANTES de adicioná-los ao layout
        self.hostname = QLineEdit()
        self.porta = QLineEdit()
        self.banco = QLineEdit()
        self.usuario = QLineEdit()
        self.senha = QLineEdit()
        self.senha.setEchoMode(QLineEdit.Password) 
        self.cod_vendedor = QLineEdit()
        self.cod_produto_servico = QLineEdit()
        self.cod_produto_entrega = QLineEdit()
        self.pagamento_entrega = QLineEdit()
        self.pagamento_online = QLineEdit()
        self.email = QLineEdit() 

        # ------------------------------------------------------------------
        # ORGANIZAÇÃO EM GRADE (4 COLUNAS)
        # ------------------------------------------------------------------

        linha = 0
        layout.addWidget(QLabel("Nome do Servidor"), linha, 0)
        layout.addWidget(self.hostname, linha, 1)
        layout.addWidget(QLabel("Vendedor Padrão"), linha, 2)
        layout.addWidget(self.cod_vendedor, linha, 3)

        linha += 1
        layout.addWidget(QLabel("Porta"), linha, 0)
        layout.addWidget(self.porta, linha, 1)
        layout.addWidget(QLabel("Produto do tipo 'Serviço' "), linha, 2)
        layout.addWidget(self.cod_produto_servico, linha, 3)

        linha += 1
        layout.addWidget(QLabel("Banco de Dados"), linha, 0)
        layout.addWidget(self.banco, linha, 1)
        layout.addWidget(QLabel("Produto do tipo 'Entrega' "), linha, 2)
        layout.addWidget(self.cod_produto_entrega, linha, 3)

        linha += 1
        layout.addWidget(QLabel("Usuário"), linha, 0)
        layout.addWidget(self.usuario, linha, 1)
        layout.addWidget(QLabel("Forma Pgto - Entrega"), linha, 2)
        layout.addWidget(self.pagamento_entrega, linha, 3)

        linha += 1
        layout.addWidget(QLabel("Senha"), linha, 0)
        layout.addWidget(self.senha, linha, 1)
        layout.addWidget(QLabel("Forma Pgto - Aplicativo"), linha, 2)
        layout.addWidget(self.pagamento_online, linha, 3)

        # ------------------------------------------------------------------
        # CAMPO EMAIL
        # ------------------------------------------------------------------

        linha += 1
        layout.addWidget(QLabel("E-mail"), linha, 0)
        layout.addWidget(self.email, linha, 1, 1, 3)

        # ------------------------------------------------------------------
        # CONFIGURAÇÃO DE LAYOUT E ESTILO
        # ------------------------------------------------------------------
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.setStyleSheet("""
        QLineEdit {
            border-radius: 5px; 
            padding: 5px;
            border: 1px solid #cccccc; 
        }
        """)

        # QDialogButtonBox
        buttons = QDialogButtonBox(QDialogButtonBox.Ok ) 
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setCenterButtons(True) 

        ok_button = buttons.button(QDialogButtonBox.Ok)

        if ok_button:
            ok_button.setText("Salvar")
            ok_button.setFixedSize(500, 35) 
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

        botoes_layout = QtWidgets.QHBoxLayout()
        botoes_layout.addWidget(buttons)

        linha += 1
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
        
        # 2. Usar a classe DatabaseValidator
        validator = DatabaseValidator(host, port, db, user, pwd)
        is_valid, error_message = validator.check_connection_and_codes(
            cod_vendedor, cod_produto_servico, cod_produto_entrega, pagamento_entrega, pagamento_online
        )

        if not is_valid:
            QMessageBox.critical(
                self, "Erro de Validação ou Conexão", error_message
            )
            return False
        
        return True

    def accept(self):
        """
        Sobrescreve o método accept (chamado pelo botão Salvar) para incluir a validação
        antes de realmente aceitar e fechar o diálogo.
        """
        if self.validate_and_save():
            super().accept()
        
    def _load_values(self):
        # A lógica de carregamento do ENV permanece aqui, pois manipula os widgets
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


# --- CLASSE GerenciadorServicos ---
class GerenciadorServicos(QtWidgets.QMainWindow,Ui_GerenciadorServicos):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Determinar caminho base da aplicação
        if getattr(sys, "frozen", False):
            self.base_dir = sys._MEIPASS
        else:
            self.base_dir = os.path.dirname(__file__)

        exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else self.base_dir
        
        self.env_path = os.path.join(exe_dir, ".env")

        self.create_default_env_if_missing()

        icon_path = os.path.join(self.base_dir, "assets", "gestor.apihub.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # --- Configuração do Novo Botão btnAtualizarApi ---
        # Como o .ui não foi modificado, vamos tentar criar o objeto
        # Se você atualizar o .ui e o apihub_ui.py, remova este bloco.
        try:
            self.btnAtualizarApi = self.findChild(QPushButton, "btnAtualizarApi")
            if not self.btnAtualizarApi:
                 # Cria o botão se ele não foi carregado pelo .ui (simulando a inclusão)
                self.btnAtualizarApi = QPushButton("🔄️ ATUALIZAR APIHUB", self.centralwidget)
                self.btnAtualizarApi.setObjectName("btnAtualizarApi")
                # Define a posição (Ajuste conforme seu layout!)
                self.btnAtualizarApi.setGeometry(QtCore.QRect(20, 170, 211, 31)) 
                self.btnAtualizarApi.setStyleSheet(self.get_update_button_style())
                self.btnAtualizarApi.setCursor(QtCore.Qt.PointingHandCursor)
                
        except Exception:
            # Garante que a variável exista, caso o findChild falhe
            self.btnAtualizarApi = QPushButton("⬇️ ATUALIZAR API", self.centralwidget)


        # Conexão de botões
        self.btnInstalar.clicked.connect(self.instalar_servicos_py) # Instala/Inicia
        self.btnServico.clicked.connect(self.on_btn_servico_click) # Parar
        self.btnEditarEnv.clicked.connect(self.on_editar_env)
        self.btnAbrirLog.clicked.connect(self.abrir_log)
        self.btnAbrirDash.clicked.connect(self.abrir_dash)
        self.btnPainel.clicked.connect(self.abrir_painel)
        self.btnLogAll.clicked.connect(self.abrir_painel_log_all)
        self.btnDesinstalar.clicked.connect(self.excluir_servicos_py)
        
        # --- CONEXÃO DO NOVO BOTÃO DE ATUALIZAÇÃO ---
        self.btnAtualizarApi.clicked.connect(self.on_btn_atualizar_api)
        # ---------------------------------------------
        
        # Configura ícones e estilos (incluindo o botão de desinstalar)
        self._setup_icons() 
        self.atualizar_status_servico()
        
    def get_update_button_style(self):
        """Estilo para o botão de atualização."""
        return """
        QPushButton {
            background-color: rgb(0, 50, 100); /* Azul escuro */
            color: rgb(255, 255, 255);        /* branco */
            font-weight: bold;
            border-radius: 5px;
            border: none;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }

        QPushButton:hover {
            background-color: rgb(0, 80, 150);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        QPushButton:pressed {
            background-color: rgb(0, 30, 80);
            padding-top: 12px;
            padding-bottom: 8px;
        }
        """

    def on_btn_atualizar_api(self):
        """Abre a janela de listagem e download de versões."""
        dialog = VersionsDialog(self)
        dialog.exec_()
        
    def _setup_icons(self):
        """Configura os ícones dos botões Instalar, Serviço e Desinstalar."""
        style = self.style()
        
        # ▶️ Botão Instalar
        play_icon = style.standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self._set_colored_icon(self.btnInstalar, play_icon)

        # ⏹️ Botão Servico
        stop_icon = style.standardIcon(QtWidgets.QStyle.SP_MediaStop)
        self._set_colored_icon(self.btnServico, stop_icon)
        
        # 🗑️ Botão Desinstalar
        try:
            # 'fa5s.trash-alt' é o ícone sólido de lixeira
            icon_trash = qta.icon('fa5s.trash-alt', color='white')
            self.btnDesinstalar.setIcon(icon_trash)
            self.btnDesinstalar.setIconSize(QtCore.QSize(20, 20))
        except Exception as e:
            print(f"Não foi possível carregar ícone qtawesome: {e}")
        
        self.btnDesinstalar.setText("Desinstalar")
        self.btnDesinstalar.setCursor(QtCore.Qt.PointingHandCursor)
        
        # REMOVI O ESTILO VERMELHO FIXO DAQUI PARA COLOCAR NA LÓGICA DE STATUS
        self.btnDesinstalar.setText("Desinstalar")
        #self.btnDesinstalar.setStyleSheet(estilo_vermelho)
        self.btnDesinstalar.setCursor(QtCore.Qt.PointingHandCursor)


    def _set_colored_icon(self, button, icon, size=QtCore.QSize(50, 50), color=QtGui.QColor("white")):
        """Auxiliar para aplicar um ícone recolorido a um botão."""
        pixmap = icon.pixmap(size)
        colored_pixmap = QtGui.QPixmap(pixmap.size())
        colored_pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(colored_pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)
        painter.end()
        button.setIcon(QtGui.QIcon(colored_pixmap))
        button.setIconSize(size)


    def on_btn_servico_click(self):
        """
        Ação para o botão btnServico: SOMENTE PARAR o serviço.
        """
        status = self.verificar_status_servico()

        if status == "Iniciado":
            # 1. Feedback visual imediato para o usuário
            self.lblStatusServico.setText("Parando...")
            self.lblStatusServico.setStyleSheet("color: orange; font-weight: bold;")
            self.btnServico.setEnabled(False) # Desabilita para não clicar 2x
            
            # Força a atualização da interface gráfica AGORA
            QtWidgets.QApplication.processEvents()
            
            # 2. Tenta parar os serviços
            parou_api = self.parar_servico(Config.SERVICE_NAME_API)
            parou_redis = self.parar_servico(Config.SERVICE_NAME_REDIS)

            # 3. Espera um pouco para o Windows processar (o "pulo do gato")
            # Serviços demoram para sair do status "STOP_PENDING" para "STOPPED"
            time.sleep(3) 

            if parou_api and parou_redis:
                QMessageBox.information(
                    self, "Sucesso", "Serviços parados com sucesso."
                )
            
            # 4. Agora sim verifica o status real
            self.atualizar_status_servico()

        elif status == "Parado":
            QMessageBox.information(
                self, "Aviso", "Os serviços já estão **Parados**. Use o botão **Instalar** para iniciá-los."
            )
            
        elif status == "Não instalado":
             QMessageBox.information(
                self, "Aviso", "O serviço não está instalado. Use o botão **Instalar** para configurar e instalar."
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Aviso", "Não foi possível determinar o status do serviço."
            )

    def verificar_status_servico(self, nome_servico=Config.SERVICE_NAME_API):
        """Verifica o status do serviço da API (vmd-api-hub)."""
        try:
            result = subprocess.run(
                ["sc", "query", nome_servico], capture_output=True, text=True
            )
            if "RUNNING" in result.stdout:
                return "Iniciado"
            elif "STOPPED" in result.stdout:
                return "Parado"
            else:
                return "Não instalado"
        except Exception:
            return "Erro"

    def atualizar_status_servico(self):
        status = self.verificar_status_servico()

        if hasattr(self, "lblStatusServico"):
            self.lblStatusServico.setText(status)
            
        style = self.style()

        # --- DEFINIÇÃO DOS ESTILOS (Para não ficar repetindo código) ---
        
        # Estilo VERMELHO (Para Stop e Desinstalar Ativo)
        estilo_vermelho = """
            QPushButton { 
                background-color: #C82333; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                border: none; 
            }
            QPushButton:hover { background-color: #e02b3c; }
            QPushButton:pressed { background-color: #a91e2c; padding-top: 12px; }
        """
        
        # Estilo CINZA (Para Desabilitados)
        estilo_cinza = """
            QPushButton { 
                background-color: rgb(140, 140, 140); 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                border: none; 
            }
        """

        # Estilo VERDE (Para Play Ativo)
        estilo_verde = """
            QPushButton { 
                background-color: green; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                border: none; 
            }
            QPushButton:hover { background-color: rgb(0, 197, 0); }
            QPushButton:pressed { background-color: rgb(0, 160, 0); padding-top: 12px; }
        """

        # Estilo VERDE CLARO (Para Play quando já iniciado/desabilitado)
        estilo_verde_claro = """
            QPushButton { 
                background-color: #81f485; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                border: none; 
            }
        """

        # --- LÓGICA DE STATUS ---

        if status == "Iniciado":
            self.lblStatusServico.setStyleSheet("color: green; font-weight: bold;")
            
            # Botão Serviço (STOP) -> Vermelho e Ativo
            self.btnServico.setStyleSheet(estilo_vermelho)
            self.btnServico.setEnabled(True)

            # Botão Instalar (PLAY) -> Verde Claro e Inativo (pois já roda)
            self.btnInstalar.setStyleSheet(estilo_verde_claro)
            self.btnInstalar.setEnabled(False) 
            
            # Botão Desinstalar -> Vermelho e Ativo
            self.btnDesinstalar.setStyleSheet(estilo_vermelho)
            self.btnDesinstalar.setEnabled(True)

            self.btnAtualizarApi.setStyleSheet(estilo_cinza)
            self.btnAtualizarApi.setEnabled(False)

        elif status == "Parado":
            self.lblStatusServico.setStyleSheet("color: orange; font-weight: bold;")
            
            # Botão Serviço (STOP) -> Cinza e Inativo (já está parado)
            self.btnServico.setStyleSheet(estilo_cinza)
            self.btnServico.setEnabled(False)

            # Botão Instalar (PLAY) -> Verde e Ativo (para Iniciar)
            self.btnInstalar.setStyleSheet(estilo_verde)
            self.btnInstalar.setEnabled(True)

            # Botão Desinstalar -> Vermelho e Ativo (Pode desinstalar se parado)
            self.btnDesinstalar.setStyleSheet(estilo_vermelho)
            self.btnDesinstalar.setEnabled(True)

            self.btnAtualizarApi.setStyleSheet(estilo_cinza)
            self.btnAtualizarApi.setEnabled(False)

        elif status == "Não instalado":
            self.lblStatusServico.setStyleSheet("color: gray; font-weight: bold;")
            
            # Botão Serviço (STOP) -> Cinza e Inativo
            self.btnServico.setStyleSheet(estilo_cinza)
            self.btnServico.setEnabled(False) 
            
            # Botão Instalar (PLAY) -> Cinza, mas com hover verde (Instalar)
            # Aqui mantivemos uma lógica especifica do seu código original para o botão instalar neste estado
            self.btnInstalar.setStyleSheet("""
                QPushButton { background-color: rgb(140, 140, 140); color: white; font-weight: bold; border-radius: 6px; border: none; }
                QPushButton:pressed { background-color: rgb(0, 197, 0); padding-top: 12px; }
                QPushButton:hover { background-color: rgb(160, 160, 160); }
            """)
            self.btnInstalar.setEnabled(True)

            #self.btnAtualizarApi.setStyleSheet(estilo_cinza)
            self.btnAtualizarApi.setEnabled(True)

            # Botão Desinstalar -> CINZA e INATIVO (Correção solicitada)
            self.btnDesinstalar.setStyleSheet(estilo_cinza)
            self.btnDesinstalar.setEnabled(False)
            
            #self.atualizar_status_servico()

        elif status == "Erro":
            self.lblStatusServico.setStyleSheet("color: red; font-weight: bold;")
            self.btnServico.setEnabled(False) 
            self.btnInstalar.setEnabled(True)
            
            # No erro, desabilita o desinstalar por segurança ou deixa cinza
            self.btnDesinstalar.setStyleSheet(estilo_cinza)
            self.btnDesinstalar.setEnabled(False)

            self.btnAtualizarApi.setStyleSheet(estilo_cinza)
            self.btnAtualizarApi.setEnabled(False)



        # Garante o tamanho dos ícones
        self.btnServico.setIconSize(QtCore.QSize(50, 50))
        self.btnInstalar.setIconSize(QtCore.QSize(50, 50))

    def create_default_env_if_missing(self):
        if os.path.exists(self.env_path):
            return

        default_env = """NODE_ENV=production
PORT=3334
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Tempo para persistir o LOG em horas | default 7 * 24 = 168
TIME_LOG=168

# CONEXÃO BD
DATABASE_URL="sqlserver://HOSTNAME:PORTA;database=BANCO;user=USUARIO;password=SENHA;trustServerCertificate=true"
COD_VENDEDOR=
COD_PRODUTO_SERVICO=
COD_PRODUTO_ENTREGA=
PAGAMENTO_ENTREGA=
PAGAMENTO_ONLINE=
EMAIL= 

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
                    val_part = val.strip()
                    if "#" in val_part:
                        val_no_comment = val_part.split("#", 1)[0].strip()
                    else:
                        val_no_comment = val_part
                    kv[key.strip()] = (val_no_comment, idx)
        return lines, kv

    def write_env_preserve(self, lines, kv_updates):
        for k, v in kv_updates.items():
            found = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith(k + "=") or stripped.split("=")[0].strip() == k:
                    comment = ""
                    if "#" in line:
                        idx_hash = line.find("#")
                        comment = line[idx_hash:]
                    lines[i] = f"{k}={v}{comment}"
                    found = True
                    break
            if not found:
                lines.append(f"{k}={v}")

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

    def iniciar_servicos_py(self):
        """Inicia os serviços vmd-api-hub e redis-service."""
        try:
            self.set_status_servico("Iniciando serviços...")
            
            print("Iniciando serviços...")
            subprocess.run(["net", "start", Config.SERVICE_NAME_API],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", Config.SERVICE_NAME_REDIS],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.set_status_servico("Iniciado")
            return True

        except subprocess.CalledProcessError as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(
                self, "Erro de Comando",
                "Falha ao iniciar o(s) serviço(s). Verifique se o app está como administrador.\n\n"
                f"Detalhes:\n{e}"
            )
            return False
        except Exception as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(self, "Erro", f"Erro inesperado durante a inicialização: {e}")
            return False

    def instalar_servicos_py(self):
        
        current_status = self.verificar_status_servico()
        
        # Se o serviço JÁ ESTÁ INSTALADO (Parado ou Iniciado), apenas tenta INICIAR.
        if current_status in ("Iniciado", "Parado"):
            
            if current_status == "Iniciado":
                 QMessageBox.information(self, "Aviso", "Os serviços já estão **Iniciados**.")
                 return
                 
            # Ação de INICIAR (quando status é Parado)
            QMessageBox.information(self, "Aviso", "Os serviços estão instalados. Tentando **iniciar** os serviços...")
            
            if self.iniciar_servicos_py():
                QMessageBox.information(self, "Sucesso!", "Serviços iniciados com sucesso!")
            else:
                 QMessageBox.warning(self, "Aviso!", "Falha ao iniciar os serviços. Verifique o log ou o status.")
            
            self.atualizar_status_servico()
            return

        # Lógica de INSTALAÇÃO (se Não Instalado)
        
        # 1. Obter caminhos
        nssm_path, vmd_api_hub_path, redis_path = self.get_service_paths()

        # 2. Verificar existência dos executáveis
        if not os.path.exists(nssm_path):
            QMessageBox.critical(self, "[ERRO]", f"nssm.exe não encontrado em {nssm_path}")
            return
        if not os.path.exists(vmd_api_hub_path):
            QMessageBox.critical(self, "[ERRO]", f"vmd-api-hub.exe não encontrado em {vmd_api_hub_path}")
            return
        if not os.path.exists(redis_path):
            QMessageBox.critical(self, "[ERRO]", f"redis-server.exe não encontrado em {redis_path}")
            return

        try:
            # 3. Instalando serviços com nssm
            self.set_status_servico("Instalando API...")
            subprocess.run([nssm_path, "install", Config.SERVICE_NAME_API, vmd_api_hub_path],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.set_status_servico("Instalando Redis...")
            subprocess.run([nssm_path, "install", Config.SERVICE_NAME_REDIS, redis_path],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # 4. Definindo para iniciar automaticamente
            self.set_status_servico("Configurando auto-start...")
            subprocess.run([nssm_path, "set", Config.SERVICE_NAME_API, "Start", "SERVICE_AUTO_START"],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run([nssm_path, "set", Config.SERVICE_NAME_REDIS, "Start", "SERVICE_AUTO_START"],
                        check=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # 5. Iniciando serviços
            if self.iniciar_servicos_py():
                self.set_status_servico("Iniciado")
                QMessageBox.information(self, "Sucesso!", "Instalação finalizada com sucesso!")
            else:
                self.set_status_servico("Parado")
                QMessageBox.warning(self, "Aviso!", "Instalação finalizada, mas falha ao iniciar os serviços. Tente iniciar manualmente.")
            
            self.atualizar_status_servico()

        except subprocess.CalledProcessError as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(
                self, "Erro de Comando",
                "Falha ao executar comando. Verifique se o app está como administrador.\n\n"
                f"Detalhes:\n{e}"
            )
        except Exception as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(self, "Erro", f"Erro inesperado durante a instalação: {e}")
            
    def excluir_servicos_py(self):
        # 1. Obter caminhos
        nssm_path, _, _ = self.get_service_paths()

        # 2. Verificar existência do nssm
        if not os.path.exists(nssm_path):
            QMessageBox.critical(self, "[ERRO]", f"nssm.exe não encontrado em {nssm_path}")
            return

        try:
            # 3. Parar serviços
            self.set_status_servico("Parando serviços...")
            subprocess.run(["net", "stop", Config.SERVICE_NAME_API], creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "stop", Config.SERVICE_NAME_REDIS], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # 4. Remover serviços com nssm
            self.set_status_servico("Removendo API...")
            subprocess.run(
                [nssm_path, "remove", Config.SERVICE_NAME_API, "confirm"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.set_status_servico("Removendo Redis...")
            subprocess.run(
                [nssm_path, "remove", Config.SERVICE_NAME_REDIS, "confirm"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.set_status_servico("Removido")
            QMessageBox.information(self, "Sucesso!", "Serviços removidos com sucesso!")
            self.atualizar_status_servico()
            
        except subprocess.CalledProcessError as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(
                self,
                "Erro de Comando",
                "Falha ao executar comando. Verifique se o app está como administrador.\n\n"
                f"Detalhes:\n{e}"
            )
        except Exception as e:
            self.set_status_servico("Erro")
            QMessageBox.critical(self, "Erro", f"Erro inesperado durante a remoção: {e}")

    def parar_servico(self, nome_servico):
        """Para um serviço específico."""
        try:
            # Não usamos check=True aqui para que o programa não quebre se o serviço
            # já estiver parado, pois 'net stop' falha nesse caso.
            subprocess.run(
                ["net", "stop", nome_servico],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Falha ao parar o serviço {nome_servico}:\n{e}"
            )
            return False

    def set_status_servico(self, status):
        """Define o texto do QLabel de status e força a atualização da UI."""
        if hasattr(self, "lblStatusServico"):
            self.lblStatusServico.setText(status)
            QtWidgets.QApplication.processEvents() 

    def abrir_log(self):
        """Abre o arquivo de log da API no programa padrão do sistema."""
        caminho_log = Config.LOG_PATH_API
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
        """Abre o dashboard local no navegador padrão."""
        url_dash = Config.URL_DASHBOARD
        try:
            webbrowser.open(url_dash)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o dashboard:\n{e}"
            )

    def abrir_painel(self):
        """Abre o ENV do Painel de Pedidos."""
        caminho_painel = Config.get_painel_env_path()
        if not caminho_painel:
            QtWidgets.QMessageBox.warning(self, "Erro", "A variável LOCALAPPDATA não está definida.")
            return

        try:
            if os.path.exists(caminho_painel):
                os.startfile(caminho_painel)
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Erro", f"O ENV do Painel de Pedidos não foi encontrado! Verifique se a instalação foi concluída corretamente e tente novamente",
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o ENV Painel de Pedidos:\n{e}"
            )
            
    def abrir_painel_log_all(self):
        """Abre o LOG Geral do Painel de Pedidos."""
        caminho_log = Config.get_painel_log_all_path()
        if not caminho_log:
            QtWidgets.QMessageBox.warning(self, "Erro", "A variável LOCALAPPDATA não está definida.")
            return

        try:
            if os.path.exists(caminho_log):
                os.startfile(caminho_log)
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Erro", f"O LOG do Painel de Pedidos não foi encontrado! Verifique se a instalação foi concluída corretamente e tente novamente!",
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Erro", f"Erro ao abrir o LOG Painel de Pedidos:\n{e}"
            )
            
    def get_service_paths(self):
        base_dir = Config.BASE_DIR_INFARMA
        
        # 1. Detectar arquitetura
        arch = platform.machine()
        nssm_subdir = "win64" if arch.endswith("64") else "win32"
            
        nssm_path = os.path.join(base_dir, "nssm", nssm_subdir, "nssm.exe")
        vmd_api_hub_path = os.path.join(base_dir, "vmd-api-hub.exe")
        redis_path = os.path.join(base_dir, "redis-server.exe")
        
        return nssm_path, vmd_api_hub_path, redis_path

   
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GerenciadorServicos()
    window.show()
    sys.exit(app.exec_())