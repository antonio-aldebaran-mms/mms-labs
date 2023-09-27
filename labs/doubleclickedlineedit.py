from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal, QEvent

"""
    QLineEdit com ação no double click
"""
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
