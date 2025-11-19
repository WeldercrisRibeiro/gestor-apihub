from PyQt5 import QtWidgets
import pyodbc

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
            
            QtWidgets.QMessageBox.warning(self, "Erro", f"Erro na conexão! Verifique os dados informados e tente novamente.")  
