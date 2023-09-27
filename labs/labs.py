import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore  import QThreadPool
from mainwindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    thread_pool = QThreadPool.globalInstance()
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())

