import sys
import random
import threading
from PySide6 import QtCore, QtWidgets, QtGui
from twisted.internet import protocol, reactor

# Gloal constants

WIN_X = 800
WIN_Y = 600

PORT = 8000

# Global Objects
simple_client = None

def close_connection():
    simple_client.transport.loseConnection()
def fetchall():
    simple_client.transport.write(b"fetchall")

class RPPCS_Main(QtWidgets.QMainWindow):
    def __init__(self):
        # Establish connection
        global simple_client
        factory = SimpleFactory()
        reactor.connectTCP("localhost", PORT, factory)
        self.t = threading.Thread(target=reactor.run, args=(False,))
        self.t.start()
        # Wait until the connection is established.
        while simple_client is None:
            pass
        
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
        test_action = QtGui.QAction("Test", self)
        test_action.setShortcut("t")
        test_action.triggered.connect(self.test)
        action_menu.addAction(test_action)

    def closeEvent(self, event):
        global simple_client
        reactor.callFromThread(close_connection)
        while simple_client is not None:
            pass
        self.t.join()
        
    @QtCore.Slot()
    def escape_key(self):
        self.close()

    @QtCore.Slot()
    def test(self):
        reactor.callFromThread(fetchall)
        
# END class RPPCS_Main


    
class SimpleClient(protocol.Protocol):
    def connectionMade(self):
        # Capture the protocol in the global variable simple_client
        # when a connection is successful.
        global simple_client
        simple_client = self

    def dataReceived(self, data):
        # As soon as any data is received, print it.
        print("Server said:", data.decode())

    def connectionLost(self, reason):
        global simple_client
        simple_client = None
        print(f"connection lost")
        
# END SimpleClient



class SimpleFactory(protocol.ClientFactory):
    protocol = SimpleClient
        
    def clientConnectionFailed(self, connector, reason):
        print("Connection failed!")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        reactor.stop()
        
# END SimpleFactory



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = RPPCS_Main()
    window.show()
    app.exec()

