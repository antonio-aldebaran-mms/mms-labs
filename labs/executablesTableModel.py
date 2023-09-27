from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QFileInfo, QUrl, QSettings, QObject, Signal, Slot, QThreadPool
from PySide6.QtWidgets import QStyledItemDelegate, QFileDialog
from PySide6.QtGui import QDesktopServices

import requests
import hashlib
import os
from urllib.parse import urlsplit
from downloader import DownloadTask
import subprocess

"""
    Classe para agrupar os parametros
"""
class Executable:
    def __init__(self, fileInfo=QFileInfo(), name=None, url=None, description="", status="", md5sum=""):
        self.fileInfo = fileInfo
        self.url = url
        self.name = name
        self.description = description
        self.status = status
        self.md5sum = md5sum
        self.error = None
"""
    Leitor url generico
"""
def load_labs_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        labs_data = response.json()
        return labs_data
    except requests.exceptions.RequestException as e:
        print(f"Error loading labs.json: {e}")
        return None

"""
    Classe para ativar o tooltip
"""
class TooltipDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        return str(value)


"""
    Classe abstrata como modelo da tabela
"""
class ExecutablesTableModel(QAbstractTableModel):

    """
        Construtor
    """
    def __init__(self):
        super(ExecutablesTableModel, self).__init__()
        self.executables = []


    """
        reimplementação QAbstractTableModel::rowCount()
    """
    def rowCount(self, index=QModelIndex()):
        return len(self.executables)


    """
        reimplementação QAbstractTableModel::columnCount()
    """
    def columnCount(self, index=QModelIndex()):
        return 4 # 3 colunas: Nome, Descrição, Type e Status


    """
        reimplementação QAbstractTableModel::headerData()
    """
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "Name"
                elif section == 1:
                    return "Description"
                elif section == 2:
                    return "Type"
                elif section == 3:
                    return "Status"


    """
        reimplementação QAbstractTableModel::data()
    """
    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            exe = self.executables[row]

            if col == 0:
                if exe.name:
                    return exe.name
                elif exe.fileInfo:
                    return exe.fileInfo.baseName()
            elif col == 1:
                return exe.description
            elif col == 2:
                if exe.fileInfo:
                    return "Application" if exe.fileInfo.suffix() == "exe" else "Python file"
                elif exe.url :
                    return "Application" if exe.url.endswith('.exe') else "Python file"
            elif col == 3:
                return exe.status
        elif role == Qt.ToolTipRole:
            exe = self.executables[index.row()]
            if index.column() == 3:
                if exe.error:
                    return exe.error
            return exe.fileInfo.absoluteFilePath() if exe.fileInfo else ""
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
            if self.executables[index.row()].status == "Download":
                return Qt.yellow
            elif self.executables[index.row()].status == "Outdated":
                return Qt.red
        elif role == Qt.ForegroundRole and index.column() == 3:
             return Qt.white
        return None


    """
        adiciona executáveis disponíveis para download a lista
    """
    def loadLabs(self, labs_url):
        labs_data = load_labs_json(labs_url)
        if labs_data:
            for lab in labs_data["labs"]:
                self.addData(url=lab.get("url"), name=lab.get("name"), description=lab.get("description"), md5sum=lab.get("hash"))


    """
        função vinculada ao single click para abrir o exe
    """
    def openExecutable(self, index):
        row = index.row()
        exe = self.executables[row]
        if exe.fileInfo and exe.fileInfo.exists():
            if exe.fileInfo.suffix() == "py":
                settings = QSettings("MiningMath", "MMLabs")
                pythonPath = settings.value("python_path", None)

                if pythonPath:
                    scriptPath = exe.fileInfo.absoluteFilePath()
                    try:
                        subprocess.Popen([pythonPath, scriptPath])
                    except Exception as e:
                        print(f"Error executing script: {e}")
                else:
                    print("Python executable path not configured.")
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(exe.fileInfo.absoluteFilePath()))


    """
        função vinculada ao double click para download
    """
    def downloadUrl(self, index):
        row = index.row()
        exe = self.executables[row]
        if exe.url and (exe.status == "Download" or exe.status == "Outdated"):
            settings = QSettings("MiningMath", "MMLabs")
            last_path = settings.value("last_path", None)
            if last_path is None:
                file_dialog = QFileDialog()
                file_dialog.setFileMode(QFileDialog.Directory)
                file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
                last_path = file_dialog.getExistingDirectory()
                settings.setValue("last_path", last_path)

            if last_path:
                url = exe.url
                filename = url.split('/')[-1]
                fullPath = os.path.join(last_path, filename)
                infoFile = QFileInfo(fullPath)
                exe.fileInfo = infoFile

                self.pool = QThreadPool.globalInstance()

                self.downloadTask = DownloadTask(url, infoFile.absoluteFilePath(), row)
                self.downloadTask.signalEmitter.progress.connect(lambda progress: self.handleDownloadProgress(progress, row))
                self.downloadTask.signalEmitter.finished.connect(lambda finished: self.handleDownloadFinished(finished, row))
                self.downloadTask.signalEmitter.error.connect(lambda error: self.handleDownloadError(error, row))
                self.pool.start(self.downloadTask)


    """
        atualiza status de acordo com o progresso do download
    """
    @Slot(float, int)
    def handleDownloadProgress(self, progress, row):
        exe = self.executables[row]
        exe.status = f"{progress}%"
        index = self.index(row, 3)
        self.dataChanged.emit(index, index)


    """
        Usado para salvar uma mensagem de erro do download
    """
    @Slot(str, int)
    def handleDownloadError(self, error, row):
        exe = self.executables[row]
        exe.error = error
        index = self.index(row, 3)
        self.dataChanged.emit(index, index)


    """
        Chamado quando o download é concluído (ou falha)
    """
    @Slot(bool, int)
    def handleDownloadFinished(self, success, row):
        exe = self.executables[row]
        if success:
            exe.status = "Updated"
            md5sum = self.calculate_md5(exe.fileInfo.absoluteFilePath())
            if md5sum != exe.md5sum:
                exe.md5sum = md5sum
        else:
            exe.status = "Download Error"
        self.dataChanged.emit(self.index(row, 3),self.index(row, 3))


    """
        Usa o md5 para verificar se o arquivo é o mesmo do servidor
    """
    def calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    """
        Adiciona dados a tabela
    """
    def addData(self, info=QFileInfo(), name=None, url="", description="", md5sum=""):
        # Evitar duplicação
        for exe in self.executables:
            if (info and exe.fileInfo and exe.fileInfo.fileName() == info.fileName()) or (url and exe.url == url):
                return

        if url:
            # Verifica se o arquivo existe localmente
            exists = False
            urlParts = urlsplit(url)
            urlList = urlParts.path.split('/')
            fName = urlList[-1]
            for exe in self.executables:
                sameFile = (exe.fileInfo and fName == exe.fileInfo.fileName())
                if sameFile:
                    if (exe.md5sum == md5sum):
                        exe.status = "Updated"
                    else:
                        exe.status = "Outdated"
                    exe.url = url
                    exe.name = name
                    exe.description = description
                    exists = True
                    break

            if exists == False:
                exe = Executable(fileInfo=None, name=name, url=url, description=description, status="Download", md5sum=md5sum)
                self.executables.append(exe)

        elif info:
            md5sum = self.calculate_md5(file_path=info.absoluteFilePath())
            exists = False
            for exe in self.executables:
                if exe.md5sum == md5sum:
                    exe.status = "Updated"
                    exe.fileInfo = info
                    exists = True
                    break
            if exists == False:
                description = "User file" if info.suffix() == "exe" else "User file"
                exe = Executable(fileInfo=info, name=info.baseName(), description=description, status="", md5sum=md5sum)
                self.executables.append(exe)

        self.layoutChanged.emit()


    """
        Remove dados da tabela
    """
    def removeData(self, fullPath):
        for row in range(len(self.executables)):
            if self.executables[row].fileInfo and self.executables[row].fileInfo.absoluteFilePath() == fullPath:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self.executables[row]
                self.endRemoveRows()
                break
        self.layoutChanged.emit()
