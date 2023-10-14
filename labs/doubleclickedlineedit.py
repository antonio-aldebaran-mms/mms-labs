# This Python file uses the following encoding: utf-8
# ------------------------------------------------------------------------------
# Copyright (c) 2023 MiningMath, miningmath@miningmath.com
# Licensed under the MIT License.
# ------------------------------------------------------------------------------
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal, QEvent

# QLineEdit com ação no double click adicionado no configPath.ui
class DoubleClickedLineEdit(QLineEdit):
    doubleClicked = Signal()

    def __init__(self, *args, **kwargs):
        super(DoubleClickedLineEdit, self).__init__(*args, **kwargs)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.MouseButtonDblClick:
                self.doubleClicked.emit()
                return True
        return super(DoubleClickedLineEdit, self).eventFilter(obj, event)
