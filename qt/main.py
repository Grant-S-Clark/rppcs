import sys
import random
import threading
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from twisted.internet import protocol, reactor

# Gloal constants

WIN_X = 800
WIN_Y = 600

PORT = 8000

# Global Objects
app = None
simple_client = None
connection_failed = False
database = None

# Networking functions.
def close_connection():
    simple_client.transport.loseConnection()
def fetchall():
    simple_client.transport.write(b"fetchall")


# Functions for fetching information from the database dictionary
def tournament_numplayers(t_id):
    return database["TT"][t_id][1]

def tournament_player_id_list(t_id):
    ret = list()
    
    for m_id in database["MT"]:
        if m_id not in database["BT"] and database["MT"][m_id][0] == t_id:
            ret.append(database["MT"][m_id][1])
            ret.append(database["MT"][m_id][2])

    return ret

class PlayerToolBox(QToolBox):
    def __init__(self, parent, p_rect, t_id):
        super().__init__(parent = parent)
        self.p_rect = p_rect
        self.t_id = t_id
        self.selection_box = QComboBox()
        current_index = 0
        for i, p_id in enumerate(tournament_player_id_list(self.t_id)):
            self.selection_box.addItem(database["PT"][p_id][0])
            if p_id == p_rect.p_id:
                current_index = i
        self.selection_box.setCurrentIndex(current_index)
            
        
        
        self.addItem(self.selection_box, "Select Player")


# Class for rectangles associated with players in a tournament.
class PlayerRect:
    def __init__(self,
                 x, y, w, h,
                 p_id, graphics_scene):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.gs = graphics_scene
        self.p_id = p_id
        self.name = database["PT"][self.p_id][0]

    def add_to_scene(self):
        self.rect = self.gs.addRect(QtCore.QRectF(self.x, self.y, self.w, self.h))
        self.text = self.gs.addText(self.name)
        self.text.setPos(self.x, self.y)

    def set_player(p_id):
        self.p_id = p_id
        self.name = database["PT"][self.p_id][0]
        self.text.setPlainText(self.name)

class TournamentGraphicsScene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent = parent)
        #self.setAcceptedMouseButtons(Qt.LeftButton)
        self.p_rects = None
        self.is_clicked = False
        self.selected = None
        
    def set_player_rects(self, p_rects):
        self.p_rects = p_rects

    def mousePressEvent(self, event):
        self.selected = None
        self.is_clicked = True
        for p_rect in self.p_rects:
            if p_rect.rect.contains(event.scenePos()):
                self.selected = p_rect
                break

        app.sendEvent(self.parent(), event)

    def mouseReleaseEvent(self, event):
        self.is_clicked = False
            
        
# Class for the main widget of the tournament mode. Will consist
# of 3 widgets, a QGraphicsScene, a QGraphicsView, and a custom
# QToolBox depending on the type of object selected on the
# QGraphicsView.
class TournamentWidget(QWidget):
    def __init__(self, parent, t_id):
        super().__init__(parent=parent)
        self.t_id = t_id
        self.setLayout(QHBoxLayout())
        self.layout = self.layout()

        self.__setup_graphics()
        self.__setup_tournament_toolbox()

    def __setup_graphics(self):
        # Create the widgets
        self.gv = QGraphicsView()
        self.gs = TournamentGraphicsScene(self)

        # Set the viewing scene
        self.gv.setSceneRect(0, 0, 800, 800)
        self.gv.setScene(self.gs)
        
        self.player_rects = list()
        # Add rectangles
        pos_x = 50
        pos_y = 20
        for i, p_id in enumerate(tournament_player_id_list(self.t_id)):
            self.player_rects.append(PlayerRect(pos_x, pos_y + i * 60, 100, 30, p_id, self.gs))

        self.gs.set_player_rects(self.player_rects)
        for p_rect in self.player_rects:
            p_rect.add_to_scene()

        # Set scroll bars to be at top right corner of scene.
        self.gv.centerOn(0, 0)
        
        # Add the view to the layout
        self.layout.addWidget(self.gv)
        # Widget 0 has stretch factor of 4.
        self.layout.setStretch(0, 4)

    def __setup_tournament_toolbox(self):
        self.tb = QToolBox()
        self.tb.addItem(QLabel("Test Item"), "Test Category")
        self.layout.addWidget(self.tb)
        # Widget 1 has stretch factor of 1.
        self.layout.setStretch(1, 1)

    def mousePressEvent(self, event):
        # Event happened in graphics scene, check to see if we need
        # to change the toolbox.        if self.gs.is_clicked:
            if isinstance(self.gs.selected, PlayerRect):
                prev = self.tb
                self.tb = PlayerToolBox(self, self.gs.selected, self.t_id)
                self.layout.replaceWidget(prev, self.tb)
                prev.close()
                
        # Also check to see if the event occurred in the currently
        # active toolbox and respond accordingly.
            
    
# Class for the main window of the program.
class RPPCS_Main(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Establish connection
        global simple_client
        factory = SimpleFactory()
        reactor.connectTCP("localhost", PORT, factory)
        self.t = threading.Thread(target=reactor.run, args=(False,))
        self.t.start()
        # Wait until the connection is established.
        # If a connection fails, print to console and exit program.
        while simple_client is None:
            if connection_failed:
                print("Error connecting to server program.")
                quit()
        # Get database info
        reactor.callFromThread(fetchall)
        while database is None:
            pass
        
        print(database) # DEBUGGING!!!!!!!!!
        
        global WIN_X, WIN_Y

        self.setWindowTitle("RPPCS")
        self.setGeometry(100, 100, WIN_X, WIN_Y)
        self.setWindowIcon(QIcon("data/cctt.png"))

        # Menu bar setup
        menu_bar = self.menuBar()
        action_menu = menu_bar.addMenu("&Actions")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Esc")
        exit_action.triggered.connect(self.escape_key)
        action_menu.addAction(exit_action)
        test_action = QAction("Test", self)
        test_action.setShortcut("t")
        test_action.triggered.connect(self.test)
        action_menu.addAction(test_action)

        # Tool bar setup
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        # "Tournaments" button
        t_button_action = QAction("&Tournaments", self)
        t_button_action.triggered.connect(self.set_central_widget_tournaments)
        toolbar.addAction(t_button_action)
        # "Players" button
        p_button_action = QAction("&Players", self)
        p_button_action.triggered.connect(self.set_central_widget_players)
        toolbar.addAction(p_button_action)
        # "Settings" button
        s_button_action = QAction("&Settings", self)
        s_button_action.triggered.connect(self.set_central_widget_settings)
        toolbar.addAction(s_button_action)

        self.set_central_widget_tournaments()

    # This function is called when the qt window is closed.
    def closeEvent(self, event):
        global simple_client
        reactor.callFromThread(close_connection)
        while simple_client is not None:
            pass
        self.t.join()
        
    def escape_key(self):
        self.close()

    def test(self):
        reactor.callFromThread(fetchall)

    def set_central_widget_tournaments(self):
        # Set the window's central widget to be the tournament editor widget
        # Parent is the main window, tournament id is zero.
        self.t_widget = TournamentWidget(parent = self, t_id = 0)
        self.setCentralWidget(self.t_widget)
            
    def set_central_widget_players(self):
        # Set the window's central widget to be the tournament editor widget.
        label = QLabel("Player Management Mode")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

    def set_central_widget_settings(self):
        # Set the window's central widget to be the tournament editor widget.
        label = QLabel("Settings Mode (TBD)")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
        
# END class RPPCS_Main


    
class SimpleClient(protocol.Protocol):
    def connectionMade(self):
        # Capture the protocol in the global variable simple_client
        # when a connection is successful.
        global simple_client
        simple_client = self

    def dataReceived(self, data):
        global database
        database = eval(data.decode())

    def connectionLost(self, reason):
        global simple_client
        simple_client = None
        print(f"connection lost")
        
# END SimpleClient



class SimpleFactory(protocol.ClientFactory):
    protocol = SimpleClient
        
    def clientConnectionFailed(self, connector, reason):
        global connection_failed
        connection_failed = True
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        reactor.stop()
        
# END SimpleFactory



if __name__ == "__main__":
    app = QApplication([])
    window = RPPCS_Main()
    window.show()
    app.exec()
