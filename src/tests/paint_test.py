'''
http://blog.rburchell.com/2010/02/pyside-tutorial-custom-widget-painting.html
'''


import sys

from PySide.QtCore import *
from PySide.QtGui import *

class CustomWidget(QWidget):
    def __init__(self, parent, anumber):
        QWidget.__init__(self, parent)
        self._number = anumber
    
    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QBrush(Qt.red, Qt.Dense2Pattern))
        p.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, str(self._number))
        p.setPen(QColor(220, 220, 220))
        p.drawText(self.rect(), Qt.AlignRight | Qt.AlignVCenter, str(self._number * 2))

class MyMainWindow(QMainWindow):
    def __init__(self, parent):
        QMainWindow.__init__(self, parent)
        # Add content
        central = CustomWidget(self, 666)
        self.setCentralWidget(central)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sw = MyMainWindow(None)
    sw.show()
    app.exec_()
    sys.exit()