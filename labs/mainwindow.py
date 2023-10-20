# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMenu, QHeaderView
from PySide6.QtCore import QFileInfo, Qt, QSettings, QUrl, QDir
from PySide6.QtGui import QIcon, QDesktopServices


"""
    to creating ui_mainwindow.py
    <python path>\\Lib\\site-packages\\PySide6\\uic.exe -g python .\\mainwindow.ui -o ui_mainwindow.py
"""
from ui_mainwindow import Ui_MainWindow

from appTableModel import AppTableModel, TooltipDelegate
from configPath import ConfigPathDialog


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Carregando formulário ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Menu file
        self.ui.addNew.triggered.connect(self.on_addExec_clicked)
        self.ui.addPy.triggered.connect(self.on_addPy_clicked)
        self.ui.configPath.triggered.connect(self.configPath)

        # Configuração da tabela
        self.model = AppTableModel()
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
        self.model.loadLabs()
        settings = QSettings("MiningMath", "MMLabs")
        lastPath = settings.value("last_path", None)
        if lastPath:
            self.path = lastPath
            self.model.loadPath(self.path)
        else:
            self.configPath()

        # configuração da janela principal
        self.setWindowTitle('MiningMath Labs')
        self.resize(800, 600)
        self.show()
        iconInfo = QFileInfo("./mms-labs/labs/labs.ico")
        self.setWindowIcon(QIcon(iconInfo.absoluteFilePath()))

        initialPython = settings.value("python_path", None)
        if initialPython == None or initialPython == "":
            pyPath = QFileInfo("./Python3/python.exe");
            settings.setValue("python_path", pyPath.absoluteFilePath())


    # ação para adicionar um executável individual fora do path
    def on_addExec_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open app', '.', 'Applications (*.exe)')

        info = QFileInfo(fname)
        if info.exists():
            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])
            pathsList.append(info.absoluteFilePath())
            settings.setValue("paths_list", pathsList)

        if fname:
            self.model.addData(info=info)


    # ação para adicionar um scrpt python individual fora do path
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


    # Configura o path onde ficam salvos os executáveis baixados
    def configPath(self, initialPath=None):

        settings = QSettings("MiningMath", "MMLabs")
        if initialPath:
            self.path = initialPath
        else:
            initialPath = settings.value("last_path", None)
            initialPython = settings.value("python_path", None)
            initialToken = settings.value("token", None)
            dialog = ConfigPathDialog(initialPath, initialPython, initialToken, self)
            result = dialog.exec()
            if result == ConfigPathDialog.Accepted:
                self.path = dialog.lePath.text()
                self.pythonPath = dialog.lePython.text()
                self.token = dialog.leToken.text()
                settings = QSettings("MiningMath", "MMLabs")
                settings.setValue("last_path", self.path)
                settings.setValue("python_path", self.pythonPath)
                settings.setValue("token", self.token)


    # clique simples para atualizar o statusBar com o path da linha selecionada
    def on_tableExecs_clicked(self, index):

        executable = self.model.data(index, Qt.ToolTipRole)
        self.statusBar().showMessage(executable)


    # ações de double click na tabela
    def on_tableExecs_doubleClicked(self, index):

        col = index.column()
        if col == 0:
            self.model.openExecutable(index)
        elif col == 3:
            self.model.downloadUrl(index)

    # menu de contexto com ações de remover exe do path, visualizar no explorer e instalar os requerimentos
    def show_context_menu(self, pos):

        selected_index = self.ui.tableExecs.selectionModel().currentIndex()
        if selected_index.isValid():
            row = selected_index.row()
            app = self.model.applications[row]
            fileInfo = app.fileInfo  # Objeto QFileInfo

            settings = QSettings("MiningMath", "MMLabs")
            pathsList = settings.value("paths_list", [])

            context_menu = QMenu(self)

            # Adiciona opção para abrir no explorador
            open_explorer_action = context_menu.addAction("Show in explorer")
            open_explorer_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(fileInfo.absolutePath())))


            # Verifica se o arquivo de requisitos existe e adiciona opção para instalá-los
            if fileInfo.suffix() == "py":
                requirements_file = QFileInfo(QDir(fileInfo.absolutePath()), 'requirements.txt')
                if requirements_file.exists():
                    install_requirements_action = context_menu.addAction("Install Requirements")
                    install_requirements_action.triggered.connect(lambda: app.installRequirements())

            if fileInfo.absoluteFilePath() in pathsList:
                delete_action = context_menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self.delete_executable(absolutePath=fileInfo.absoluteFilePath()))

            context_menu.exec_(self.ui.tableExecs.viewport().mapToGlobal(pos))

    # ação de deletear um executável da lista individual para o menu de contexto
    def delete_executable(self, absolutePath):
        settings = QSettings("MiningMath", "MMLabs")
        pathsList = settings.value("paths_list", [])

        updatedPathsList = [path for path in pathsList if path != absolutePath]
        settings.setValue("paths_list", updatedPathsList)

        self.model.removeData(fullPath=absolutePath)
