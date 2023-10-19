# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtCore import QFileInfo, QSettings, QDir
from downloader import GithubRepositoryDownloader
import os
import subprocess

# Classe para agrupar os informações de uma linha da tabela
class Application:
    def __init__(self, dir="", fileInfo=QFileInfo(), description="", status="", hash="", github=False, date=""):
        self.fileInfo = QFileInfo(fileInfo)
        self.dir = dir
        self.description = description
        self.status = status
        self.hash = hash
        self.github = github
        self.date = date
        self.error = None
        self.downloader = GithubRepositoryDownloader("antonio-aldebaran-mms", "mms-labs", "master")

    # preparação para executar, instala os requerimentos do app, verifica o ambiente virtual e cria o ui*.py
    def installRequirements(self):
        directory = self.fileInfo.absolutePath()
        venvPath = QFileInfo(QDir(directory), 'venv').absoluteFilePath()
        venvInfo = QFileInfo(venvPath)
        print("verifica venv", venvInfo.absoluteFilePath())
        if not venvInfo.exists() :
            self.createVenv()

        requirementsPath = QFileInfo(QDir(directory), 'requirements.txt').absoluteFilePath()  # Path para o arquivo requirements.txt
        # Se existir um arquivo requirements.txt, instalar as dependências
        if os.path.exists(requirementsPath):
            pipPath = os.path.join(venvPath, 'bin', 'pip') if os.name != 'nt' else os.path.join(venvPath, 'Scripts', 'pip.exe')
            try:
                subprocess.run([pipPath, 'install', '-r', requirementsPath], check=True)
                print(f"Dependencies installed from {requirementsPath}")
                self.compileUiFiles()
            except Exception as e:
                print(f"Error installing dependencies: {e}")
                return
        else:
            print("No requirements.txt file found. Skipping dependency installation.")

    # cria o diretório virtual para o app
    def createVenv(self):
        directory = self.fileInfo.absolutePath()
        venvPath = os.path.join(directory, 'venv')  # Diretório onde o venv será criado
        venvInfo = QFileInfo(venvPath)
        if (venvInfo.exists()) :
            return

        settings = QSettings("MiningMath", "MMLabs")
        pythonPath = settings.value("python_path", None)

        # Criar o ambiente virtual
        try:
            subprocess.run([pythonPath, '-m', 'venv', venvPath], check=True)
            print(f"Virtual environment created at {venvPath}")
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            return

        requirementsPath = os.path.join(directory, 'requirements.txt')  # Path para o arquivo requirements.txt
        reqInfo = QFileInfo(requirementsPath)
        if (reqInfo.exists()) :
            self.installRequirements()

    # Compila todos os arquivos .ui no diretório especificado usando o uic.exe dentro do ambiente virtual associado.
    def compileUiFiles(self):

        # Verifica se o diretório contém um ambiente virtual
        venv_dir = QDir(self.fileInfo.absolutePath())
        if not venv_dir.cd("venv"):
            print("Não foi encontrado um ambiente virtual neste diretório.")
            return

        # Verifica se o uic.exe existe no ambiente virtual
        uicInfo = QFileInfo(venv_dir.absoluteFilePath("Lib/site-packages/PySide6/uic.exe"))
        if not uicInfo.exists():
            print(f"uic.exe não foi encontrado em {uicInfo.absoluteFilePath()}.")
            return

        # Volta ao diretório original para procurar por arquivos .ui
        venv_dir.cdUp()

        # Procura por arquivos .ui no diretório
        uiFiles = venv_dir.entryList(["*.ui"], QDir.Files)
        if not uiFiles:
            print("Não foram encontrados arquivos .ui neste diretório.")
            return

        # Compila cada arquivo .ui
        for uiFile in uiFiles:
            input_file_info = QFileInfo(venv_dir, uiFile)
            output_file = venv_dir.absoluteFilePath(f"ui_{input_file_info.baseName()}.py")

            # Comando para compilar o arquivo .ui
            cmd = [uicInfo.absoluteFilePath(), "-g", "python", input_file_info.absoluteFilePath(), "-o", output_file]

            try:
                # Executa o comando
                subprocess.run(cmd, check=True)
                print(f"Arquivo {uiFile} compilado com sucesso para {output_file}.")
            except subprocess.CalledProcessError as e:
                print(f"Erro ao compilar o arquivo {uiFile}: {e}.")




    # ler o arquivo readme para construir a descrição
    def getFileReadmeContent(self):

        directory = self.fileInfo.absolutePath()

        # Verificar se o diretório existe
        if not os.path.exists(directory):
            print("The provided directory does not exist.")
            return None

        # Montar o caminho completo para o arquivo README
        readme_path = os.path.join(directory, "README.md")

        # Verificar se o arquivo README existe
        if not os.path.isfile(readme_path):
            print("README.md file does not exist in the provided directory.")
            return None

        # Ler e retornar o conteúdo do arquivo README
        with open(readme_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
