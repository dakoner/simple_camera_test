import sys
#sys.path.append("..")
#import mvsdk
import signal
from PyQt6 import QtWidgets, QtGui
from main_window import MainWindow


class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)    
    main_window = MainWindow()
    main_window.show()#showMaximized()
    app.exec()
