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
datetime = None

# Networking functions.
def close_connection():
    simple_client.transport.loseConnection()
def fetchall():
    simple_client.transport.write(b"fetchall")
def db_instruction(ins):
    simple_client.transport.write(ins.encode())


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

class TournamentCreationWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent = None) # So it is a window
        self.parent = parent
        self.setLayout(QGridLayout())
        self.layout = self.layout()
        self.name_label = QLabel("Tournament Name:")
        self.name_entry = QLineEdit()
        self.count_label = QLabel("Number of Players:")
        self.count_entry = QLineEdit()
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.submit_tournament)
        
        self.layout.addWidget(self.name_label, 0, 0)
        self.layout.addWidget(self.name_entry, 0, 1)
        self.layout.addWidget(self.count_label, 1, 0)
        self.layout.addWidget(self.count_entry, 1, 1)
        self.layout.addWidget(self.create_button, 2, 0)

        self.setWindowTitle("Create Tournament")
        self.setWindowIcon(QIcon("data/cctt.png"))
        
    def submit_tournament(self):
        # Invalid Name Checks
        name = self.name_entry.text().strip()
        if name == "":
            return

        for t_id in database["TT"]:
            if database["TT"][t_id][0] == name:
                return
        
        try:
            num_players = int(self.count_entry.text())
        except ValueError:
            return

        # Pull an unused tournament id
        t_ids = set(database["TT"].keys())
        new_id = 0
        while new_id in t_ids:
            new_id += 1

        # Separation using pipes so I can do split() with '|'
        ins = f"create|tournament|{new_id}|{name}|{num_players}"
        global datetime
        datetime = None
        reactor.callFromThread(db_instruction, ins)
        
        while datetime is None: # Wait for database communication.
            pass

        print("DATETIME =", datetime)
        
        # Insert into local database.
        # TODO

        # Close self and tell parent that it closed
        self.parent.temp_window = None

# END class TournamentCreationWindow

class PlayerToolBox(QToolBox):
    def __init__(self, parent, p_rect, t_id):
        super().__init__(parent = parent)
        self.p_rect = p_rect
        self.t_id = t_id
        self.selection_box = QComboBox()
        self.m_rect = None # match rectangle this player is associated with.
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

# END class PlayerToolBox


class GameWidget(QWidget):
    def __init__(self, parent, g_id):
        super().__init__(parent = parent)
        self.g_id = g_id
        self.p1_score = database["GT"][self.g_id][1]
        self.p2_score = database["GT"][self.g_id][2]
        self.setLayout(QGridLayout())
        self.layout = self.layout()
        self.p1_label = QLabel(f"P1 Score: {self.p1_score}", self)
        self.p2_label = QLabel(f"P2 Score: {self.p2_score}", self)
        self.p1_plus = QPushButton("+", self)
        self.p2_plus = QPushButton("+", self)
        self.p1_minus = QPushButton("-", self)
        self.p2_minus = QPushButton("-", self)

        self.p1_plus.clicked.connect(self.p1_plus_pressed)
        self.p2_plus.clicked.connect(self.p2_plus_pressed)
        self.p1_minus.clicked.connect(self.p1_minus_pressed)
        self.p2_minus.clicked.connect(self.p2_minus_pressed)
        
        self.layout.addWidget(self.p1_label, 0, 0)
        self.layout.addWidget(self.p1_plus, 1, 0)
        self.layout.addWidget(self.p1_minus, 1, 1)
        
        self.layout.addWidget(self.p2_label, 2, 0)
        self.layout.addWidget(self.p2_plus, 3, 0)
        self.layout.addWidget(self.p2_minus, 3, 1)

    def p1_plus_pressed(self):
        if self.p1_score == 11:
            return
        self.p1_score += 1
        database["GT"][self.g_id][1] += 1
        ins = f"UPDATE games SET p1_score = {self.p1_score} WHERE id = {self.g_id}"
        reactor.callFromThread(db_instruction, ins)
        self.p1_label.setText(f"P1 Score: {self.p1_score}")
        
    def p2_plus_pressed(self):
        if self.p2_score == 11:
            return
        self.p2_score += 1
        database["GT"][self.g_id][2] += 1
        ins = f"UPDATE games SET p2_score = {self.p2_score} WHERE id = {self.g_id}"
        reactor.callFromThread(db_instruction, ins)
        self.p2_label.setText(f"P2 Score: {self.p2_score}")
        
    def p1_minus_pressed(self):
        if self.p1_score == 0:
            return
        self.p1_score -= 1
        database["GT"][self.g_id][1] -= 1
        ins = f"UPDATE games SET p1_score = {self.p1_score} WHERE id = {self.g_id}"
        reactor.callFromThread(db_instruction, ins)
        self.p1_label.setText(f"P1 Score: {self.p1_score}")
        
    def p2_minus_pressed(self):
        if self.p2_score == 0:
            return
        self.p2_score -= 1
        database["GT"][self.g_id][2] -= 1
        ins = f"UPDATE games SET p2_score = {self.p2_score} WHERE id = {self.g_id}"
        reactor.callFromThread(db_instruction, ins)
        self.p2_label.setText(f"P2 Score: {self.p2_score}")

# END class GameWidget

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

        self.p1_select.currentTextChanged.connect(self.p1_selection_changed)
        self.p2_select.currentTextChanged.connect(self.p2_selection_changed)

        # Set up the 7 game tabs with their respective widgets.
        game_ids = list()
        for g_id in database["GT"]:
            if self.m_rect.m_id == database["GT"][g_id][0]:
                game_ids.append(g_id)

        self.game_tabs = list()
        for g_id in game_ids:
            self.game_tabs.append(GameWidget(self, g_id))

        for i, g_widget in enumerate(self.game_tabs):
            self.addItem(g_widget, f"Game {i + 1}")

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

    def p1_selection_changed(self, text):
        self.m_rect.set_player1(player_name_to_id(text))
    def p2_selection_changed(self, text):
        self.m_rect.set_player2(player_name_to_id(text))

# END class MatchToolBox


class TournamentRenameWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent = parent)
        self.parent = parent # For calling parent functions.
        self.selection_list = QListWidget()
        self.label = QLabel("Rename Selected:")
        self.line_edit = QLineEdit()
        self.setLayout(QVBoxLayout())
        self.layout = self.layout()

        self.selected = None
        self.t_ids = list()
        for i, t_id in enumerate(database["TT"]):
            self.t_ids.append(t_id)
            self.selection_list.addItem(database["TT"][t_id][0])
        self.selection_list.itemPressed.connect(self.list_selection_changed)
        self.line_edit.editingFinished.connect(self.edit_tournament_name)

        self.layout.addWidget(self.selection_list)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        
    def list_selection_changed(self, item):
        selected = self.selection_list.row(item)
        if selected == self.selected:
            return
        self.selected = selected
        self.line_edit.setText(item.text())

    def edit_tournament_name(self):
        if self.selected is None:
            return
        
        new_name = self.line_edit.text()

        self.selection_list.item(self.selected).setText(new_name)
        database["TT"][self.t_ids[self.selected]][0] = new_name
        ins = f"UPDATE tournaments SET name = '{new_name}' WHERE id = {self.t_ids[self.selected]}"
        reactor.callFromThread(db_instruction, ins)

        # Update the tournament name in the selection list in
        # the parent toolbox.
        self.parent.setup_selection_box()

# END class TournamentRenameWidget


class TournamentToolBox(QToolBox):
    def __init__(self, parent, t_id):
        super().__init__(parent = parent)
        self.t_id = t_id
        self.selection_box = None
        self.setup_selection_box()
        self.rename_widget = TournamentRenameWidget(self)
        self.addItem(self.rename_widget, "Rename Tournanents")
        
    def setup_selection_box(self):
        old = None
        if self.selection_box is not None:
            old = self.selection_box
            
        selection_box = QComboBox()
        
        current_index = 0
        selection_box.addItem("None")
        for i, t_id in enumerate(database["TT"]):
            selection_box.addItem(database["TT"][t_id][0])
            if t_id == self.t_id:
                current_index = i + 1
        
        selection_box.setCurrentIndex(current_index)

        if old is None:
            self.selection_box = selection_box
            self.addItem(self.selection_box, "Select Tournament")
        else:
            self.removeItem(0)
            old.close()
            self.selection_box = selection_box
            self.insertItem(0, self.selection_box, "Select Tournament")
            
        self.selection_box.currentTextChanged.connect(self.tournament_selection_changed)
        
    def tournament_selection_changed(self, text):
        global current_tournament_id
        current_tournament_id = tournament_name_to_id(text)
        self.t_id = current_tournament_id
        self.parent().update_tournament()

# END class TournamentToolBox


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
        database["MT"][self.m_id][1] = p_id
        ins = f"UPDATE matches SET p1_id = {p_id} WHERE id = {self.m_id}"
        reactor.callFromThread(db_instruction, ins)
        string = database["PT"][self.p1_id][0] + " V.S. " + database["PT"][self.p2_id][0]
        self.text.setPlainText(string)

    def set_player2(self, p_id):
        self.p2_id = p_id
        database["MT"][self.m_id][2] = p_id
        ins = f"UPDATE matches SET p2_id = {p_id} WHERE id = {self.m_id}"
        reactor.callFromThread(db_instruction, ins)
        string = database["PT"][self.p1_id][0] + " V.S. " + database["PT"][self.p2_id][0]
        self.text.setPlainText(string)

# END class MatchRect


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
        self.m_rect = None # match rectangle this player is associated with.

    def add_to_scene(self):
        self.rect = self.gs.addRect(QtCore.QRectF(self.x, self.y, self.w, self.h))
        self.text = self.gs.addText(self.name)
        self.text.setPos(self.x, self.y)

    def set_player(self, p_id):
        # Only perform changes if necessary
        if p_id != self.p_id:
            old = self.p_id
            self.p_id = p_id
            self.name = database["PT"][self.p_id][0]
            self.text.setPlainText(self.name)
            # Edit the match player selection list.
            if self.m_rect.p1_id == old:
                self.m_rect.set_player1(p_id)
            else:
                self.m_rect.set_player2(p_id)
            

    def set_match_rect(self, m_rect):
        self.m_rect = m_rect

# END class PlayerRect

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
            
# END class TournamentGraphicsScene


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
                    self.player_rects[i * 2].set_match_rect(self.match_rects[-1])
                    self.player_rects[i * 2 + 1].set_match_rect(self.match_rects[-1])
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

# END class TournamentWidget


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

        self.temp_window = None
        
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
        create_tournament_action = QAction("Create Tournament", self)
        create_tournament_action.triggered.connect(self.create_tournament)
        action_menu.addAction(create_tournament_action)

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

    def create_tournament(self):
        if self.temp_window is not None:
            self.temp_window.close()
        self.temp_window = TournamentCreationWindow(self)
        self.temp_window.show()
        
        
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
        decoded = data.decode()
        if decoded[:9] == "datetime=":
            global datetime
            datetime = decoded[9:]
        else:
            global database
            if database is None:
                database = eval(decoded)
            else:
                print(decoded)
                print()

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
