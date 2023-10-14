# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtCore import Signal, QRunnable, QObject, QThreadPool, QSettings, QFileInfo, QDir, QDateTime, Qt
import requests
import os
import json
import base64
from urllib.parse import urlparse

# A classe DonwloadTask não consegue emitir sinais diretamente, precisa desta subclasse
class SignalEmitter(QObject):

    progress = Signal(float, int)
    finished = Signal(bool, int)
    error = Signal(str, int)

 # Classe para efetuar o donwload em uma thread separada, evitando bloqueio da interface
class DownloadTask(QRunnable):

    def __init__(self, url, filepath, row):
        super().__init__()
        self.url = url
        self.row = row
        self.filepath = filepath
        self.signalEmitter = SignalEmitter()

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()

            print(self.url)
            print(self.filepath)
            with open(self.filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

            self.signalEmitter.finished.emit(True, self.row)
        except Exception as e:
            self.signalEmitter.error.emit(f"{e}", self.row)
            self.signalEmitter.finished.emit(False, self.row)


class GithubRepositoryDownloader(QObject):

    def __init__(self, user, repo, branch):
        self.pool = QThreadPool.globalInstance()
        self.user = user
        self.repo = repo
        self.branch = branch
        self.signalEmitter = SignalEmitter()
        self.sendData = Signal(str, str, str, str)
        settings = QSettings("MiningMath", "MMLabs")
        self.token = settings.value("token", None)
        if not self.token:
            print("Acess limited on 60 per hour")
            return
        else:
            self.headers = {
                'Authorization': f'token {self.token}',
            }

    # retorna a lista de arquivos de um app no github
    def getFilesInDirectory(self, dir):
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/contents/{dir}?ref={self.branch}"
        if (self.headers) :
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)
        files = []

        if response.status_code == 200:
            contents = json.loads(response.text)
            for item in contents:
                if item['type'] == 'file':
                    files.append(item['download_url'])

        return files

    # cria o filePath local para um salvar o arquivo online no github
    def getFilePathFromUrl(self, dir, url):
        path = urlparse(url).path
        fileName = os.path.basename(path)
        return QFileInfo(QDir(dir), fileName).absoluteFilePath()

    # realiza o download dos arquivos de um app/dir
    def downloadFiles(self, dir, index):
        settings = QSettings("MiningMath", "MMLabs")
        lastPath = settings.value("last_path", None)
        if not lastPath:
            print("Last path is not set.")
            return

        dirPath = QFileInfo(QDir(lastPath), dir).absoluteFilePath()
        directory = QDir(dirPath)
        print(lastPath, dir, dirPath)
        if not directory.exists():
             QDir().mkpath(dirPath)

        files = self.getFilesInDirectory(dir)
        self.maxfiles = len(files)
        if self.maxfiles <= 0:
            return

        self.currentProgress = 0
        for file_url in files:
            filePath = self.getFilePathFromUrl(dir=dirPath, url=file_url)
            self.downloadTask = DownloadTask(file_url, filePath, index)
            self.downloadTask.signalEmitter.progress.connect(lambda progress: self.handleDownloadProgress(progress, index))
            self.downloadTask.signalEmitter.finished.connect(lambda finished: self.handleDownloadFinished(finished, index))
            self.downloadTask.signalEmitter.error.connect(lambda error: self.handleDownloadError(error, index))
            self.pool.start(self.downloadTask)

        self.handleDownloadFinished(True, index)
        commitHash = self.getCommitHash(dir=dir)
        commitDate = self.getCommitDate(dir=dir)
        self.saveCommitDataToFile(commitData=str(commitHash + ", " + commitDate), dir=dir)

    def handleDownloadProgress(self, progress, index):
        print(f"Index {index}: Download Progress {progress}%")

    def handleDownloadFinished(self, finished, index):
        self.signalEmitter.progress.emit((self.currentProgress / self.maxfiles) * 100, index)
        if (self.currentProgress >= self.maxfiles):
            self.signalEmitter.finished.emit(finished, index)
        self.currentProgress += 1

    def handleDownloadError(self, error, index):
        self.signalEmitter.error.emit(error, index)

    # retorna os diretórios no repositório, é esperado que cada reposítorio seja um app
    def getRepositoryDirectories(self):
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/contents?ref={self.branch}"
        if (self.headers) :
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)
        directories = []
        print(url,  response)

        if response.status_code == 200:
            contents = json.loads(response.text)
            print(contents)
            for item in contents:
                if item['type'] == 'dir':  # Verifica se o item é um diretório
                    directories.append(item['path'])

        return directories

    # commit date do gihub
    def getCommitDate(self, dir):
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/commits?path={dir}&sha={self.branch}"
        if (self.headers) :
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)

        if response.status_code == 200:
            commits = json.loads(response.text)
            if commits:
                latest_commit = commits[0]  # o primeiro commit na resposta é o mais recente
                commit_date = latest_commit['commit']['committer']['date']
                return commit_date

        return None

    # commit hash do github
    def getCommitHash(self, dir):
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/commits?path={dir}&sha={self.branch}"
        if (self.headers) :
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)

        if response.status_code == 200:
            commits = json.loads(response.text)
            if commits:
                latest_commit = commits[0]  # o primeiro commit na resposta é o mais recente
                hash = latest_commit['sha']
                return hash

            return None

    # coluna descrição do app fica no readme.md no github
    def getReadmeContent(self, dir):
        url = f"https://api.github.com/repos/{self.user}/{self.repo}/contents/{dir}/README.md?ref={self.branch}"
        if (self.headers) :
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)

        if response.status_code == 200:
            content_data = json.loads(response.text)
            if 'content' in content_data:
                encoded_content = content_data['content']
                decoded_content = base64.b64decode(encoded_content).decode('utf-8')
                return decoded_content

    # salva localmente o arquivo para comparação com github afim de saber se precisa atualizar
    def saveCommitDataToFile(self, commitData, dir):
        try:
            settings = QSettings("MiningMath", "MMLabs")
            lastPath = settings.value("last_path", None)
            dirPath  = QFileInfo(QDir(lastPath), dir).absoluteFilePath()
            filename = QFileInfo(QDir(dirPath), "commit.txt").absoluteFilePath()
            with open(filename, "w") as file:
                file.write(commitData)
        except Exception as e:
            print(f"{e}")
            return ""

    # captura o hash salvo no commit.txt criado a partir dos dados do github
    def getLocalHash(self, dir) :
        try :
            settings = QSettings("MiningMath", "MMLabs")
            lastPath = settings.value("last_path", None)
            dirPath  = QFileInfo(QDir(lastPath), dir).absoluteFilePath()
            filename = QFileInfo(QDir(dirPath), "commit.txt").absoluteFilePath()
            with open(filename, "r") as file:
                localCommitData = file.readline().strip()

            localHash, localDate = localCommitData.split(", ")
            return localHash
        except Exception as e:
            print(f"{e}")
            return ""

    # captura o date salvo no commit.txt criado a partir dos dados do github
    def getLocalDate(self, dir) :
        try :
            settings = QSettings("MiningMath", "MMLabs")
            lastPath = settings.value("last_path", None)
            dirPath  = QFileInfo(QDir(lastPath), dir).absoluteFilePath()
            filename = QFileInfo(QDir(dirPath), "commit.txt").absoluteFilePath()
            with open(filename, "r") as file:
                localCommitData = file.readline().strip()

                localHash, localDate = localCommitData.split(", ")
                return localDate
        except Exception as e:
            print(f"{e}")
            return ""

    # compara os valores salvos localmente com os do github para verificar se há uma versão nova
    def isGithubCommitNewer(self, dir):
        localCommitData = None
        try :
            settings = QSettings("MiningMath", "MMLabs")
            lastPath = settings.value("last_path", None)
            dirPath  = QFileInfo(QDir(lastPath), dir).absoluteFilePath()
            filename = QFileInfo(QDir(dirPath), "commit.txt").absoluteFilePath()
            with open(filename, "r") as file:
                localCommitData = file.readline().strip()

            githubDate = self.getCommitDate(dir)
            githubHash = self.getCommitHash(dir)

            print("githubDate", githubDate)
            print("githubHash", githubHash)
            print("localCommitData", localCommitData)

            if not localCommitData or not githubDate or not githubHash:
                print("Erro ao obter dados do commit.")
                return False

            localHash, localDate = localCommitData.split(", ")

            localDate = QDateTime.fromString(localDate, Qt.ISODate)
            githubDate = QDateTime.fromString(githubDate, Qt.ISODate)

            print("localhash", localHash)
            print("githubHash", githubHash)
            print("githubDate", githubDate.toString(Qt.ISODate))
            print("localDate", localDate.toString(Qt.ISODate))

            return githubHash == localHash and githubDate <= localDate
        except Exception as e:
            print(f"{e}")
            return ""

