import sys
import random
import threading
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from twisted.internet import protocol, reactor

# Gloal constants

WIN_X = 1000
WIN_Y = 600

PORT = 8000

# Global Objects
app = None
simple_client = None
connection_failed = False
database = None
current_tournament_id = None

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

def tournament_match_id_list(t_id):
    ret = list()

    for m_id in database["MT"]:
        if database["MT"][m_id][0] == t_id:
            ret.append(m_id)
    
    return ret

def tournament_name_to_id(name):
    for t_id in database["TT"]:
        if database["TT"][t_id][0] == name:
            return t_id
    return None

def player_name_to_id(name):
    for p_id in database["PT"]:
        if database["PT"][p_id][0] == name:
            return p_id
    return None

class PlayerToolBox(QToolBox):
    def __init__(self, parent, p_rect, t_id):
        super().__init__(parent = parent)
        self.p_rect = p_rect
        self.t_id = t_id
        self.selection_box = QComboBox()
        current_index = 0
        for i, p_id in enumerate(database["PT"]):
            self.selection_box.addItem(database["PT"][p_id][0])
            if p_id == p_rect.p_id:
                current_index = i
                
        self.selection_box.setCurrentIndex(current_index)
        
        self.addItem(self.selection_box, "Select Player")

        self.selection_box.currentTextChanged.connect(self.selection_changed)

    def selection_changed(self, text):
        self.p_rect.set_player(player_name_to_id(text))

class MatchToolBox(QToolBox):
    def __init__(self, parent, m_rect, t_id):
        super().__init__(parent = parent)
        self.m_rect = m_rect
        self.t_id = t_id
        self.p1_select = QComboBox()
        self.p2_select = QComboBox()
        
        # Allow for only selection of players from
        # children matches.
        if self.m_rect.m_id in database["BT"]:
            p1_index = 0
            p2_index = 0
            l_player_ids = self.__get_binary_tree_left_child_player_ids()
            for i, p_id in enumerate(l_player_ids):
                self.p1_select.addItem(database["PT"][p_id][0])
                if p_id == self.m_rect.p1_id:
                    p1_index = i
            r_player_ids = self.__get_binary_tree_right_child_player_ids()
            for i, p_id in enumerate(r_player_ids):
                self.p2_select.addItem(database["PT"][p_id][0])
                if p_id == self.m_rect.p2_id:
                    p2_index = i
            self.p1_select.setCurrentIndex(p1_index)
            self.p2_select.setCurrentIndex(p2_index)
            
        # Do not allow for selection of players, they are
        # set by the player_rects that are associated with this
        # match rectangle.
        else:
            self.p1_select.addItem(database["PT"][self.m_rect.p1_rect.p_id][0])
            self.p2_select.addItem(database["PT"][self.m_rect.p2_rect.p_id][0])
            self.p1_select.setEditable(False)
            self.p2_select.setEditable(False)

        self.addItem(self.p1_select, "Select Player 1")
        self.addItem(self.p2_select, "Select Player 2")

        # REMEMBER TO HANDLE INDEX CHANGE EVENTS!!!!!

    def __get_binary_tree_left_child_player_ids(self):
        ret = list()
        ret.append(None) # Always allow for selection of null player.
        lchild = database["BT"][self.m_rect.m_id][0] # left child id
        ret.append(database["MT"][lchild][1])
        ret.append(database["MT"][lchild][2])
        
        return ret

    def __get_binary_tree_right_child_player_ids(self):
        ret = list()
        ret.append(None) # Always allow for selection of null player.
        rchild = database["BT"][self.m_rect.m_id][1] # right child id
        ret.append(database["MT"][rchild][1])
        ret.append(database["MT"][rchild][2])
        
        return ret
    
    # END class MatchToolBox

class TournamentToolBox(QToolBox):
    def __init__(self, parent, t_id):
        super().__init__(parent = parent)
        self.t_id = t_id
        self.selection_box = QComboBox()
        current_index = 0
        self.selection_box.addItem("None")
        for i, t_id in enumerate(database["TT"]):
            self.selection_box.addItem(database["TT"][t_id][0])
            if t_id == self.t_id:
                current_index = i + 1
        
        self.selection_box.setCurrentIndex(current_index)
        
        self.addItem(self.selection_box, "Select Tournament")

        self.selection_box.currentTextChanged.connect(self.selection_changed)

    def selection_changed(self, text):
        global current_tournament_id
        current_tournament_id = tournament_name_to_id(text)
        self.t_id = current_tournament_id
        self.parent().update_tournament()


# Class for rectangles associated with players in a tournament.
class MatchRect:
    def __init__(self,
                 x, y, w, h,
                 m_id, graphics_scene,
                 p1_rect = None, p2_rect = None):
        # If the player rects are None, then this match is on the
        # binary tree and the players need to be grabbed from
        # the matches it originates from.
        
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.gs = graphics_scene
        self.m_id = m_id
        self.p1_rect = p1_rect
        self.p2_rect = p2_rect
        
        self.p1_id = database["MT"][self.m_id][1]
        self.p2_id = database["MT"][self.m_id][2]

    def add_to_scene(self):
        self.rect = self.gs.addRect(QtCore.QRectF(self.x, self.y, self.w, self.h))
        string = database["PT"][self.p1_id][0] + " V.S. " + database["PT"][self.p2_id][0]
        self.text = self.gs.addText(string)
        self.text.setPos(self.x, self.y)

    def set_player1(self, p_id):
        self.p1_id = p_id
        string = database["PT"][self.p1_id][0] + " V.S. " + database["PT"][self.p2_id][0]
        self.text.setPlainText(string)

    def set_player2(self, p_id):
        self.p2_id = p_id
        string = database["PT"][self.p1_id][0] + " V.S. " + database["PT"][self.p2_id][0]
        self.text.setPlainText(string)

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

    def set_player(self, p_id):
        self.p_id = p_id
        self.name = database["PT"][self.p_id][0]
        self.text.setPlainText(self.name)

class TournamentGraphicsScene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent = parent)
        #self.setAcceptedMouseButtons(Qt.LeftButton)
        self.p_rects = None
        self.m_rects = None
        self.is_clicked = False
        self.selected = None
        
    def set_player_rects(self, p_rects):
        self.p_rects = p_rects

    def set_match_rects(self, m_rects):
        self.m_rects = m_rects

    def mousePressEvent(self, event):
        self.selected = None
        self.is_clicked = True
        if self.p_rects is not None:
            for p_rect in self.p_rects:
                if p_rect.rect.contains(event.scenePos()):
                    self.selected = p_rect
                    break
            
            # if player rects exist, the match rects also exist.
            if self.selected is None:
                for m_rect in self.m_rects:
                    if m_rect.rect.contains(event.scenePos()):
                        self.selected = m_rect
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
        self.gv = None
        self.t_id = t_id
        self.setLayout(QHBoxLayout())
        self.layout = self.layout()

        self.setup_graphics()
        self.setup_tournament_toolbox()

    def setup_graphics(self):
        # Create the widgets
        prev = self.gv
        self.gv = QGraphicsView()
        self.gs = TournamentGraphicsScene(self)

        # Set the viewing scene
        self.gv.setSceneRect(0, 0, 800, 800)
        self.gv.setScene(self.gs)

        if self.t_id != None:
            # Add player rectangles
            self.player_rects = list()
            pos_x = 50
            pos_y = 20
            w = 100
            h = 30
            for i, p_id in enumerate(tournament_player_id_list(self.t_id)):
                self.player_rects.append(PlayerRect(pos_x, pos_y + i * 60, w, h, p_id, self.gs))

            self.gs.set_player_rects(self.player_rects)
            for p_rect in self.player_rects:
                p_rect.add_to_scene()

            # Add match rectangles.
            self.match_rects = list()
            pos_x += w + 40
            start_y = 20 + h # starting position of player rects plus the height of the rects.
            pos_y = start_y
            w += 120
            # Height (h) remains 30.
            n = len(self.player_rects) // 2
            first_matches = True
            print("DEBUG DATA IN setup_graphics():")
            print("num_matches =", len(tournament_match_id_list(self.t_id)))
            print("num_players =", len(self.player_rects))
            print("n =", n)
            for i, m_id in enumerate(tournament_match_id_list(self.t_id)):
                if (first_matches):
                    self.match_rects.append(MatchRect(pos_x, pos_y,
                                                      w, h, m_id, self.gs,
                                                      self.player_rects[i * 2],
                                                      self.player_rects[i * 2 + 1]))
                else:
                    self.match_rects.append(MatchRect(pos_x, pos_y,
                                                      w, h, m_id, self.gs))
                if (i == n - 1):
                    pos_x += w + 40
                    start_y += 60
                    pos_y = start_y
                    n = round(n / 2)
                    first_matches = False
                else:
                    pos_y += 120 # move down two rectangles 

            self.gs.set_match_rects(self.match_rects)
            for m_rect in self.match_rects:
                m_rect.add_to_scene()

            
        # Set scroll bars to be at top right corner of scene.
        self.gv.centerOn(0, 0)

        if prev is None:
            # Add the view to the layout
            self.layout.addWidget(self.gv)
            # Widget 0 has stretch factor of 4.
            self.layout.setStretch(0, 4)
        else:
            self.layout.replaceWidget(prev, self.gv)
            prev.close()

    def setup_tournament_toolbox(self):
        self.tb = TournamentToolBox(self, self.t_id)
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

        elif isinstance(self.gs.selected, MatchRect):
            prev = self.tb
            self.tb = MatchToolBox(self, self.gs.selected, self.t_id)
            self.layout.replaceWidget(prev, self.tb)
            prev.close()

        else:
            prev = self.tb
            self.tb = TournamentToolBox(self, current_tournament_id)
            self.layout.replaceWidget(prev, self.tb)
            prev.close()
            
        # Also check to see if the event occurred in the currently
        # active toolbox and respond accordingly.

    def update_tournament(self):
        if current_tournament_id != self.t_id or True:
            self.t_id = current_tournament_id
            self.setup_graphics()
    
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
        self.t_widget = TournamentWidget(parent = self, t_id = current_tournament_id)
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
