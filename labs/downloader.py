# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Signal, QRunnable, QObject
import requests

"""
    A classe DonwloadTask não consegue emitir sinais diretamente, precisa desta subclasse
"""
class SignalEmitter(QObject):

    progress = Signal(float, int)
    finished = Signal(bool, int)
    error = Signal(str, int)

"""
    Classe para efetuar o donwload em uma thread separada, evitando bloqueio da interface
"""
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
            totalLength = int(response.headers.get('content-length', 0))
            downloadedBytes = 0
            lastProgress = int(-1)
            chunkSize = 1024*4;
            with open(self.filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunkSize):
                    if chunk:
                        file.write(chunk)
                        downloadedBytes += len(chunk)
                        progressPercentage = int( float(downloadedBytes / totalLength) * 100)
                        if lastProgress < progressPercentage :
                            self.signalEmitter.progress.emit(progressPercentage, self.row)
                            lastProgress = progressPercentage


            self.signalEmitter.finished.emit(True, self.row)
        except Exception as e:
            self.signalEmitter.error.emit(f"{e}", self.row)
            self.signalEmitter.finished.emit(False, self.row)


