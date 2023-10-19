import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui

WIN_X = 800
WIN_Y = 600

class RPPCS_Main(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        global WIN_X, WIN_Y

        self.setWindowTitle("RPPCS")
        self.setGeometry(100, 100, WIN_X, WIN_Y)
        self.setWindowIcon(QtGui.QIcon("data/cctt.png"))
        
        menu_bar = self.menuBar()
        action_menu = menu_bar.addMenu("&Actions")
        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Esc")
        exit_action.triggered.connect(self.escape_key)
        action_menu.addAction(exit_action)


    @QtCore.Slot()
    def escape_key(self):
        quit()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = RPPCS_Main()
    window.show()

    sys.exit(app.exec())

