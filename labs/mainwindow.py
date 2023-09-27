import os
import re
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMenu, QHeaderView
from PySide6.QtCore import QFileInfo, Qt, QSettings
from PySide6.QtGui import QIcon

from executablesTableModel import ExecutablesTableModel, TooltipDelegate

"""
    para gerar o ui_mainwindow.py use o comando
    C:\\Python310\\Lib\\site-packages\\PySide6\\uic.exe -g python .\\mainwindow.ui -o ui_mainwindow.py
"""
from ui_mainwindow import Ui_MainWindow

from configPath import ConfigPathDialog

class MainWindow(QMainWindow):

    """
        construtor
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Carregando formulário ui, atualizar com `pyside6-uic.exe .\mainwindow.ui -o ui_mainwindow.py`
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Menu file
        self.ui.addNew.triggered.connect(self.on_addExec_clicked)
        self.ui.addPy.triggered.connect(self.on_addPy_clicked)
        self.ui.configPath.triggered.connect(self.configPath)

        # Configuração da tabela
        self.model = ExecutablesTableModel()
        self.ui.tableExecs.setModel(self.model)
        self.ui.tableExecs.clicked.connect(self.on_tableExecs_clicked)
        self.ui.tableExecs.doubleClicked.connect(self.on_tableExecs_doubleClicked)
        self.ui.tableExecs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableExecs.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.tableExecs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ui.tableExecs.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ui.tableExecs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.ui.tableExecs.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.ui.tableExecs.setItemDelegate(TooltipDelegate())


        # Leitura dos executáveis para tabela,
        self.model.loadLabs(labs_url="http://localhost/mmlabsnews.json")
        settings = QSettings("MiningMath", "MMLabs")
        lastPath = settings.value("last_path", None)
        if lastPath:
            self.path = lastPath
            self.loadPath()
        else:
            self.configPath()

        # configuração da janela principal
        self.setWindowTitle('MiningMath Labs')
        self.resize(800, 600)
        self.show()
        self.setWindowIcon(QIcon("labs.ico"))

    """
        ação para adicionar um executável individual fora do path
    """
    def on_addExec_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open executable', '.', 'Executables (*.exe)')

        info = QFileInfo(fname)
        if info.exists():
            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])
            pathsList.append(info.absoluteFilePath())
            settings.setValue("paths_list", pathsList)

        if fname:
            self.model.addData(info=info)


    """
        ação para adicionar um scrpt python individual fora do path
    """
    def on_addPy_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open python scripts', '.', 'Scripts (*.py)')

        info = QFileInfo(fname)
        if info.exists():
            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])
            pathsList.append(info.absoluteFilePath())
            settings.setValue("paths_list", pathsList)

        if fname:
            self.model.addData(info=info)


    """
        Configura o path onde ficam salvos os executáveis baixados
    """
    def configPath(self, initialPath=None):

        settings = QSettings("MiningMath", "MMLabs")
        if initialPath:
            self.path = initialPath
        else:
            initialPath = settings.value("last_path", None)
            initialPython = settings.value("python_path", None)
            dialog = ConfigPathDialog(initialPath, initialPython, self)
            result = dialog.exec()
            if result == ConfigPathDialog.Accepted:
                self.path = dialog.lePath.text()
                self.pythonPath = dialog.lePython.text()
                settings = QSettings("MiningMath", "MMLabs")
                settings.setValue("last_path", self.path)
                settings.setValue("python_path", self.pythonPath)

    """
        Adiciona na tabela os executáveis que estão no diretório salvo
    """
    def loadPath(self):
        if self.path:
            for root, dirs, files in os.walk(self.path):
                for file in files:
                    if file.endswith('.exe'):
                        fileInfo = QFileInfo(os.path.join(root, file))
                        self.model.addData(info=fileInfo)
                    elif file.endswith('.py'):
                        pattern = re.compile(r"if\s+__name__\s+==\s+'__main__':")
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            contents = f.read()
                            if pattern.search(contents):
                                fileInfo = QFileInfo(filepath)
                                self.model.addData(info=fileInfo)

            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])

            for path in pathsList:
                self.model.addData(info=QFileInfo(path))


    """
        clique simples para atualizar o statusBar com o path da linha selecionada
    """
    def on_tableExecs_clicked(self, index):

        executable = self.model.data(index, Qt.ToolTipRole)
        self.statusBar().showMessage(executable)


    """
        ações de double click na tabela
    """
    def on_tableExecs_doubleClicked(self, index):

        col = index.column()
        if col == 0:
            self.model.openExecutable(index)
        elif col == 3:
            self.model.downloadUrl(index)

    """
        menu de contexto para remover executáveis adicionado individualmente
    """
    def show_context_menu(self, pos):

        selected_index = self.ui.tableExecs.selectionModel().currentIndex()
        if selected_index.isValid():
            row = selected_index.row()
            fileInfo = self.model.executables[row].fileInfo  # Objeto QFileInfo

            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])

            if fileInfo.absoluteFilePath() in pathsList:
                context_menu = QMenu(self)
                delete_action = context_menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self.delete_executable(absolutePath=fileInfo.absoluteFilePath()))
                context_menu.exec_(self.ui.tableExecs.viewport().mapToGlobal(pos))

    """
        ação de deletear um executável da lista individual para o menu de contexto
    """
    def delete_executable(self, absolutePath):
        settings = QSettings("MiningMath", "MMLabs")
        pathsList = settings.value("paths_list", [])

        updatedPathsList = [path for path in pathsList if path != absolutePath]
        settings.setValue("paths_list", updatedPathsList)

        self.model.removeData(fullPath=absolutePath)
