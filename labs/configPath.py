# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtWidgets import QDialog, QFileDialog

"""
    to creating ui_configPath.py
    <python path>\\Lib\\site-packages\\PySide6\\uic.exe -g python .\\configPath.ui -o ui_configPath.py
"""
from ui_configPath import Ui_ConfigPath


# Caixa de dialogo para configurar o path dos scripts python e o exe do python que executará os scripts
class ConfigPathDialog(QDialog, Ui_ConfigPath):

    def __init__(self, initial_path=None, initial_python=None, initial_token=None, parent=None):
        super(ConfigPathDialog, self).__init__(parent)
        self.setupUi(self)

        self.leToken.setText(initial_token or "")

        # path para salvar os scripts
        self.lePath.setText(initial_path or "")
        self.pbPath.clicked.connect(self.selectFolder)
        self.lePath.doubleClicked.connect(self.selectFolder)

        # caminho do python que executará os scripts
        self.lePython.setText(initial_python or "")
        self.pbPython.clicked.connect(self.selectPython)
        self.lePython.doubleClicked.connect(self.selectPython)

    def selectFolder(self):
        new_path = QFileDialog.getExistingDirectory(self, "Select directory to load applications")
        if new_path:
            self.lePath.setText(new_path)

    def selectPython(self):
        fname, _  = QFileDialog.getOpenFileName(self, 'Open python', '.', 'python (python*.exe)')
        if fname:
            self.lePython.setText(fname)
