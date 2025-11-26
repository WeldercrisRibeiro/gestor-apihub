# 🚀 Gerenciador de Serviços -- Infarma APIHUB

Este projeto é um **Gerenciador de Serviços em Python (PyQt5)** criado
para facilitar a instalação, configuração e manutenção da aplicação
**Infarma APIHUB** no Windows.\
Ele gerencia serviços via **NSSM**, realiza configurações do ambiente e
permite atualizar a API de forma simples.

## 📌 Principais Funcionalidades

### 🔧 1. Instalação e Controle de Serviços

O sistema utiliza o **NSSM (Non-Sucking Service Manager)** para
gerenciar dois serviços essenciais:

-   **vmd-api-hub** (API principal)\
-   **redis-service** (Redis)

Com ele, é possível:

-   Instalar serviços
-   Iniciar serviços
-   Parar serviços
-   Remover serviços

Tudo diretamente pela interface gráfica.

### 📝 2. Editor de Configuração (.env)

O gerenciador possui um editor visual que permite configurar:

-   Conexão com o **SQL Server**
-   Códigos de parâmetros:
    -   Código do vendedor
    -   Códigos de produtos (serviço/entrega)
    -   Códigos de pagamento

O sistema **valida automaticamente**: - A conexão com o SQL Server - A
existência dos códigos nas tabelas corretas

### ⬆️ 3. Atualização Automática da API

O gerenciador:

-   Acessa o repositório GitHub `WeldercrisRibeiro/infarma-apihub`
-   Lista as **releases disponíveis**
-   Baixa a versão mais recente do `vmd-api-hub.exe`
-   Permite substituir o executável atual com segurança

### 📂 4. Acessos Rápidos

A interface conta com atalhos diretos para:

-   Logs da API
-   Dashboard local
-   Arquivos de configuração
-   Logs do Painel de Pedidos

## 🛠️ Requisitos para Execução

### 1. Requisitos do Sistema

  -----------------------------------------------------------------------
  Requisito                         Descrição
  --------------------------------- -------------------------------------
  **Administrador**                 O programa **deve ser executado como
                                    administrador**, já que o NSSM
                                    interage com serviços do Windows.

  **ODBC Driver**                   Necessário instalar o **Microsoft
                                    ODBC Driver 17 para SQL Server**,
                                    utilizado pelo `pyodbc`.

  **NSSM**                          O arquivo `nssm.exe` deve estar
                                    disponível na pasta do projeto.
  -----------------------------------------------------------------------

### 2. Dependências Python

Instale as dependências principais:

    pip install pyodbc==5.3.0 PyQt5==5.15.11 pyqt5_sip==12.17.1
    pip install qtawesome requests

### 3. Estrutura de Diretórios Esperada

O gerenciador espera que a API esteja instalada em:

    C:\INFARMA\APIHUB
    │
    ├── vmd-api-hub.exe          (Executável da API)
    ├── redis-server.exe         (Servidor Redis)
    └── nssm
        ├── win32
    nssm.exe
        └── win64
    nssm.exe       (Versão recomendada para Windows 64 bits)

## ▶️ Como Executar o Gerenciador

1.  Instale todas as dependências Python.
2.  Instale o **Instalador oficial do APIHUB** (disponível no GitHub).
3.  Abra seu editor (VS Code etc.) **como Administrador**.
4.  Execute o arquivo:

```
python main.py
```

## Como fazer alterações na interface?

1. Abra o arquivo `main.py`.
2. Faça as alterações necessárias.
3. Salve o arquivo.
4. Execute o arquivo novamente:

```
python main.py
```

