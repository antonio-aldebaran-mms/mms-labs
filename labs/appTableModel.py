# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QFileInfo, QUrl, QSettings, Slot
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QDesktopServices

import os
import re
import subprocess
from application import Application
from downloader import GithubRepositoryDownloader


# Classe para ativar o tooltip
class TooltipDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        return str(value)


# Classe abstrata para tabela e manipulação dos dados dos aplicativos
class AppTableModel(QAbstractTableModel):

    def __init__(self):
        super(AppTableModel, self).__init__()
        self.applications = []
        # para listar os diretórios
        self.downloader = GithubRepositoryDownloader("antonio-aldebaran-mms", "mms-labs", "master")
        self.headers = ["Name", "Description", "Type", "Status"]

    # reimplementação QAbstractTableModel::rowCount()
    def rowCount(self, index=QModelIndex()):
        return len(self.applications)


    # reimplementação QAbstractTableModel::columnCount()
    def columnCount(self, index=QModelIndex()):
        return len(self.headers)


    # reimplementação QAbstractTableModel::headerData() para customizar os titulos
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]
            else :
                return section

    # reimplementação QAbstractTableModel::data()
    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            app = self.applications[row]

            if col == 0:
                return app.dir
            elif col == 1:
                return app.description
            elif col == 2:
                if app.fileInfo:
                    return "Application" if app.fileInfo.suffix() == "exe" else "Python file"
                elif app.github:
                    return "Python file"
            elif col == 3:
                return app.status
        elif role == Qt.ToolTipRole:
            app = self.applications[index.row()]
            if index.column() == 3:
                if app.error:
                    return app.error
            return app.fileInfo.absoluteFilePath() if app.fileInfo else ""
        elif role == Qt.TextAlignmentRole and index.column() == 3:
            # Alinha o texto da coluna de status no centro
            return Qt.AlignCenter
        elif role == Qt.ItemIsSelectable and index.column() == 32:
            # Torna as células da coluna de status selecionáveis
            return True
        elif role == Qt.ItemIsEditable and index.column() == 3:
            # Torna as células da coluna de status editáveis
            return True
        elif role == Qt.BackgroundRole and index.column() == 3:
            # Define a cor de fundo da coluna de status
            if self.applications[index.row()].status == "Download":
                return Qt.yellow
            elif self.applications[index.row()].status == "Outdated":
                return Qt.red
        elif role == Qt.ForegroundRole and index.column() == 3:
             return Qt.white
        return None

    # função vinculada ao double click para abrir o app
    def openExecutable(self, index):
        row = index.row()
        app = self.applications[row]
        if app.fileInfo and app.fileInfo.exists():
            if app.fileInfo.suffix() == "py":
                scriptPath = app.fileInfo.absoluteFilePath()

                venvPath = os.path.join(app.fileInfo.absolutePath(), 'venv')
                venvInfo = QFileInfo(venvPath)
                if not venvInfo.exists() :
                    app.createVenv()

                try:
                    command = os.path.join(venvPath, "Scripts", "activate.bat") + " && python " + scriptPath
                    print(command)
                    subprocess.Popen(command, shell=True)
                except Exception as e:
                    print(f"Error executing script: {e}")
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(app.fileInfo.absoluteFilePath()))


    # função vinculada ao double click para download
    def downloadUrl(self, index):
        row = index.row()
        app = self.applications[row]
        if app.github and (app.status == "Download" or app.status == "Outdated"):
            if app.downloader:
                app.downloader.signalEmitter.progress.connect(lambda progress: self.handleDownloadProgress(progress, row))
                app.downloader.signalEmitter.finished.connect(lambda finished: self.handleDownloadFinished(finished, row))
                app.downloader.signalEmitter.error.connect(lambda error: self.handleDownloadError(error, row))
                app.downloader.downloadFiles(app.dir, row)


    # atualiza status de acordo com o progresso do download
    @Slot(float, int)
    def handleDownloadProgress(self, progress, row):
        app = self.applications[row]
        app.status = f"{progress:.1f}"
        index = self.index(row, 3)
        self.dataChanged.emit(index, index)


    # Usado para salvar uma mensagem de erro do download
    @Slot(str, int)
    def handleDownloadError(self, error, row):
        app = self.applications[row]
        app.error = error
        index = self.index(row, 3)
        self.dataChanged.emit(index, index)


    # Chamado quando o download é concluído (ou falha)
    @Slot(bool, int)
    def handleDownloadFinished(self, success, row):
        app = self.applications[row]
        if success: # '{:.3f}'.format(my_float)
            if app.status and app.status != "Download" and app.status != "OutDate" and float(app.status) > 98.0:
                app.installRequirements()
            app.status = "Updated"
            app.hash = app.downloader.getLocalHash(dir=app.dir)
            print("Sucesso download", app.hash)

        else:
            app.status = "Download Error"
        index = self.index(row, 3)
        self.dataChanged.emit(index, index)

    # Adiciona dados a tabela
    def addData(self, github=False, fileInfo=QFileInfo(), dir=None, description=None, hash=None, date=None):
        newApp = Application(dir=dir, fileInfo=fileInfo, description=description, github=github, hash=hash, date=date)
        dirInfo = QFileInfo()

        if fileInfo.suffix() == "exe" :
            app = Application(dir=fileInfo.baseName(), fileInfo=fileInfo, description="User app", status="Local file")
            self.applications.append(app)
            return

        if fileInfo:
            dirInfo = QFileInfo(fileInfo.absolutePath())


        if newApp.github:
            # Verifica se o arquivo existe localmente
            exists = False
            for app in self.applications:
                sameFile = (app.dir and newApp.dir == app.dir)
                if sameFile:
                    if self.downloader.isGithubCommitNewer(dir):
                        app.status = "Updated"
                    else:
                        app.status = "Outdated"

                    if fileInfo: app.fileInfo = fileInfo
                    if date: app.date = date
                    if dir: app.dir = dir
                    if description: app.description = description
                    exists = True
                    break

            if exists == False:
                newApp.status = "Download"
                self.applications.append(newApp)

        else:

            exists = False

            if not description:
                description = newApp.getFileReadmeContent()

            for app in self.applications:
                if dirInfo.exists() and app.dir == dir:
                    if self.downloader.isGithubCommitNewer(dir):
                        app.status = "Updated"
                    else:
                        app.status = "Outdated"

                    if description: app.description = description
                    if fileInfo: app.fileInfo = fileInfo
                    if date: app.date = date
                    if dir: app.dir = dir
                    exists = True
                    break

            if exists == False:

                if not description:
                    description = "User file" if fileInfo.suffix() == "exe" else "User python script"

                newApp.description = "description"
                newApp.hash = self.downloader.getLocalHash(dir)
                self.applications.append(newApp)

        self.layoutChanged.emit()


    # Remove dados da tabela
    def removeData(self, fullPath):
        for row in range(len(self.applications)):
            if self.applications[row].fileInfo and self.applications[row].fileInfo.absoluteFilePath() == fullPath:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self.applications[row]
                self.endRemoveRows()
                break
        self.layoutChanged.emit()


    def loadLabs(self):
        directories = self.downloader.getRepositoryDirectories()
        print(directories)
        if directories:
            for dir in directories:
                date = self.downloader.getCommitDate(dir)
                hash = self.downloader.getCommitHash(dir)
                description = self.downloader.getReadmeContent(dir)
                self.addData(github=True, dir=dir, description=description, hash=hash, date=date)


    # Adiciona na tabela os executáveis que estão no diretório salvo
    def loadPath(self, path=None):
        if not path:
            return

        for root, dirs, files in os.walk(path):
            # Calcula a profundidade do diretório atual
            depth = root[len(path):].count(os.path.sep)

            # Ignora os diretórios venv e aprofundamento além do segundo nível
            dirs[:] = [d for d in dirs if 'venv' not in d.lower() and depth < 2]

            for file in files:
                if file.endswith('.exe'):
                    fileInfo = QFileInfo(os.path.join(root, file))
                    rootInfo = QFileInfo(root)
                    self.addData(github=False, fileInfo=fileInfo, dir=rootInfo.baseName())
                elif file.endswith('.py'):
                    pattern = re.compile(r"if\s+__name__\s+==\s+[\"']__main__[\"']:")
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        contents = f.read()
                        if pattern.search(contents):
                            fileInfo = QFileInfo(filepath)
                            rootInfo = QFileInfo(root)
                            print("load local " + fileInfo.absoluteFilePath())
                            self.addData(github=False, fileInfo=fileInfo, dir=rootInfo.baseName())

        settings = QSettings("MiningMath", "MMLabs")
        pathsList = settings.value("paths_list", [])

        for path in pathsList:
            fileInfo = QFileInfo(path)
            rootInfo = QFileInfo(fileInfo.absolutePath())
            self.addData(fileInfo=QFileInfo(path), dir=rootInfo.baseName())
