import logging
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import QObject, pyqtSignal

class QTextEditLogger(logging.Handler, QObject):
    append_text = pyqtSignal(str)

    def __init__(self, parent: QTextEdit):
        super().__init__()
        QObject.__init__(self)
        self.widget = parent
        self.widget.setReadOnly(True)
        self.append_text.connect(self.widget.append)

    def emit(self, record):
        msg = self.format(record)
        self.append_text.emit(msg) 