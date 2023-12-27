# Authors:
#     Grant Clark
#     Sude Gundogan
#
# Date:
#     December 27th, 2023


# pip install --user twisted
from twisted.internet import protocol, reactor
import sqlite3

DEFAULT_PORT = 17380
port = None
db = None # Will be set later.

# Translate all tables into a dictionary of 2 dimensional lists.
"""
ret["TT"] = [T]ournament [T]able dictionary
ret["MT"] = [M]atch [T]able dictionary
ret["GT"] = [G]ame [T]able dictionary
ret["PT"] = [P]layer [T]able dictionary
ret["BT"] = match [B]inary [T]ree table dictionary

ret["TT"][id] = [ name, numplayers, date ]
ret["MT"][id] = [ t_id, p1_id, p2_id ]
ret["GT"][id] = [ m_id, p1_score, p2_score ]
ret["PT"][id] = [ name, skill ]
ret["BT"][parent_id] = [ l_child_id, r_child_id ]
"""
def fetchall():
    global db
    cur = db.cursor()
    
    ret = dict()

    cur.execute("SELECT * FROM tournaments")
    ret["TT"] = dict()
    for row in cur:
        ret["TT"][row[0]] = list(row)[1:]

    cur.execute("SELECT * FROM matches")
    ret["MT"] = dict()
    for row in cur:
        ret["MT"][row[0]] = list(row)[1:]

    cur.execute("SELECT * FROM games")
    ret["GT"] = dict()
    for row in cur:
        ret["GT"][row[0]] = list(row)[1:]
    
    cur.execute("SELECT * FROM players")
    ret["PT"] = dict()
    for row in cur:
        ret["PT"][row[0]] = list(row)[1:]

    cur.execute("SELECT * FROM match_tree")
    ret["BT"] = dict()
    for row in cur:
        ret["BT"][row[0]] = list(row)[1:]
    
    return ret

def create_debug_testing_data():
    global db

    cur = db.cursor()

    # CREATE TEST TOURNEMENT
    cur.execute("INSERT INTO tournaments (id, name, numplayers, date) VALUES (?, ?, ?, DATE('now'))",
                (0, "TestTournament0", 4)) # Values in a tuple
    db.commit()

    # CREATE TEST PLAYERS
    for i in range(4):
        cur.execute("INSERT INTO players (id, name, skill) VALUES (?, ?, 0)",
                    (i, f"TestPlayer{i}"))
        db.commit()

    
    # CREATE MATCHES
    cur.execute("""INSERT INTO matches (id, t_id, p1_id, p2_id) VALUES
                   (0, 0, 0, 1),
                   (1, 0, 2, 3),
                   (2, 0, NULL, NULL)""")
    db.commit()

    # CREATE GAMES
    game_id = 0
    for i in range(7):
        cur.execute(f"INSERT INTO games (id, m_id, p1_score, p2_score) VALUES ({game_id}, 0, 0, 0)")
        game_id += 1
    for i in range(7):
        cur.execute(f"INSERT INTO games (id, m_id, p1_score, p2_score) VALUES ({game_id}, 1, 0, 0)")
        game_id += 1
    for i in range(7):
        cur.execute(f"INSERT INTO games (id, m_id, p1_score, p2_score) VALUES ({game_id}, 2, 0, 0)")
        game_id += 1
    db.commit()

    # CREATE BINARY TREE ENTRY
    cur.execute("INSERT INTO match_tree (parent_id, l_child_id, r_child_id) VALUES (2, 0, 1)")
    db.commit()

def get_match_game_id_lists(matches : int):
    m_ids = list()
    g_ids = list()

    taken_matches = set()
    taken_games = set()
    
    global db
    cur = db.cursor()
    cur.execute("SELECT * FROM matches")
    for row in cur:
        taken_matches.add(row[0]) # NEED TO CAST TO INT?

    cur.execute("SELECT * FROM games")
    for row in cur:
        taken_games.add(row[0]) # NEED TO CAST TO INT?

    i = 0
    while len(m_ids) < matches:
        if i not in taken_matches:
            m_ids.append(i)
        i += 1

    i = 0
    while len(g_ids) < matches * 7:
        if i not in taken_games:
            g_ids.append(i)
        i += 1

    return m_ids, g_ids

def create_tournament(t_id : int, name : str, players : int):
    if players % 2 == 1:
        players += 1
    
    matches = players - 1

    global db
    cur = db.cursor()

    # Create tournament
    cur.execute("INSERT INTO tournaments (id, name, numplayers, date) VALUES (?, ?, ?, DATE('now'))",
                (t_id, name, players))
    db.commit()

    # Get valid id numbers from the database
    m_ids, g_ids = get_match_game_id_lists(matches)
    # Create matches
    m_i = 0
    g_i = 0
    
    # Matches originating from players
    last_odd_id0 = None
    last_odd_id1 = None
    for i in range(players // 2):
        cur.execute("INSERT INTO matches (id, t_id, p1_id, p2_id) VALUES (?, ?, NULL, NULL)",
                    (m_ids[m_i], t_id))
        db.commit()
        
        if (players // 2) % 2 == 1 and i == (players // 2) - 1:
            last_odd_id0 = m_ids[m_i]
                
        for j in range(7):
            cur.execute("INSERT INTO games (id, m_id, p1_score, p2_score) VALUES (?, ?, 0, 0)",
                        (g_ids[g_i], m_ids[m_i]))
            g_i += 1
        m_i += 1
        db.commit()

    last_col_count = players // 2
    matches -= last_col_count
    is_straggler_col = False
    # Rest of the matches
    while matches > 0:
        match_col_count = last_col_count // 2
            
        for i in range(match_col_count):
            cur.execute("INSERT INTO matches (id, t_id, p1_id, p2_id) VALUES (?, ?, NULL, NULL)",
                        (m_ids[m_i], t_id))
            db.commit()
            cur.execute("INSERT INTO match_tree (parent_id, l_child_id, r_child_id) VALUES (?, ?, ?)",
                        (m_ids[m_i], m_ids[m_i - last_col_count + i], m_ids[m_i - last_col_count + i + 1]))
            db.commit()

            if matches == 2 or (match_col_count % 2 == 1 and i == match_col_count - 1 and match_col_count != 1):
                if last_odd_id0 is None:
                    last_odd_id0 = m_ids[m_i]
                elif last_odd_id1 is None:
                    last_odd_id1 = m_ids[m_i]
                    is_straggler_col = True

            for j in range(7):
                cur.execute("INSERT INTO games (id, m_id, p1_score, p2_score) VALUES (?, ?, 0, 0)",
                            (g_ids[g_i], m_ids[m_i]))
                g_i += 1
            m_i += 1
            db.commit()

        # Account for straggler match
        if not is_straggler_col and last_odd_id0 is not None and last_odd_id1 is not None:
            cur.execute("INSERT INTO matches (id, t_id, p1_id, p2_id) VALUES (?, ?, NULL, NULL)",
                        (m_ids[m_i], t_id))
            db.commit()
            cur.execute("INSERT INTO match_tree (parent_id, l_child_id, r_child_id) VALUES (?, ?, ?)",
                        (m_ids[m_i], last_odd_id1, last_odd_id0))
            db.commit()
            last_odd_id0 = None
            last_odd_id1 = None
            for j in range(7):
                cur.execute("INSERT INTO games (id, m_id, p1_score, p2_score) VALUES (?, ?, 0, 0)",
                            (g_ids[g_i], m_ids[m_i]))
                g_i += 1

            # if this match is another straggler match, mark it as such.
            if match_col_count % 2 == 0:
                last_odd_id0 = m_ids[m_i]
            
            m_i += 1
            db.commit()
            match_col_count += 1 # We added a match
        
        is_straggler_col = False
        last_col_count = match_col_count
        matches -= last_col_count

    return

def create_player(p_id : int, name : str, skill : int):
    global db
    cur = db.cursor()
    cur.execute("INSERT INTO players (id, name, skill) VALUES (?, ?, ?)",
                (p_id, name, skill))
    db.commit()
    return

def delete_player(p_id : int):
    global db
    cur = db.cursor()
    cur.execute(f"DELETE FROM players WHERE id = {p_id}")
    db.commit()
    return

def delete_tournament(t_id : int):
    global db
    cur = db.cursor()
    cur.execute(f"DELETE FROM tournaments WHERE id = {t_id}")
    db.commit()
    return

def init():
    global db
    db = sqlite3.connect("rppcs_data.db")
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    db.commit()
    
    # Tournament table
    cur.execute("""CREATE TABLE IF NOT EXISTS tournaments(id         INT UNSIGNED NOT NULL PRIMARY KEY,
                                                          name       TEXT NOT NULL,
                                                          numplayers INT UNSIGNED NOT NULL,
                                                          date       DATE NOT NULL)""")

    # Player table
    cur.execute("""CREATE TABLE IF NOT EXISTS players(id      INT UNSIGNED PRIMARY KEY,
                                                      name    TEXT NOT NULL,
                                                      skill   SMALLINT UNSIGNED NOT NULL)""")

    db.commit()
    
    # Match table
    cur.execute("""CREATE TABLE IF NOT EXISTS matches(id      INT UNSIGNED NOT NULL PRIMARY KEY,
                                                      t_id    INT UNSIGNED NOT NULL,
                                                      p1_id   INT UNSIGNED,
                                                      p2_id   INT UNSIGNED,
                                                      FOREIGN KEY (t_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                                                      FOREIGN KEY (p1_id) REFERENCES players(id) ON DELETE SET NULL,
                                                      FOREIGN KEY (p2_id) REFERENCES players(id) ON DELETE SET NULL)""")
    db.commit()
    
    # Game table
    cur.execute("""CREATE TABLE IF NOT EXISTS games(id         INT UNSIGNED NOT NULL PRIMARY KEY,
                                                    m_id       INT UNSIGNED NOT NULL,
                                                    p1_score   TINYINT UNSIGNED NOT NULL,
                                                    p2_score   TINYINT UNSIGNED NOT NULL,
                                                    FOREIGN KEY (m_id) REFERENCES matches(id) ON DELETE CASCADE)""")
    
    # Match binary tree
    cur.execute("""CREATE TABLE IF NOT EXISTS match_tree(parent_id      INT UNSIGNED NOT NULL PRIMARY KEY,
                                                         l_child_id     INT UNSIGNED NOT NULL,
                                                         r_child_id     INT UNSIGNED NOT NULL,
                                                         FOREIGN KEY (parent_id) REFERENCES matches(id) ON DELETE CASCADE,
                                                         FOREIGN KEY (l_child_id) REFERENCES matches(id) ON DELETE CASCADE,
                                                         FOREIGN KEY (r_child_id) REFERENCES matches(id) ON DELETE CASCADE)""")
    db.commit()
    
    # Insert the null player into the players table if necessary.
    # Null player will have an id of NULL (translates to None).
    res = cur.execute("SELECT * FROM players WHERE id IS NULL")
    if res.fetchone() is None:
        cur.execute("INSERT INTO players (id, name, skill) VALUES (NULL, 'N/A', 0)")
        
    db.commit()
    

class SimpleServer(protocol.Protocol):
    def connectionMade(self):
        print("Client has connected to the server.")

    def connectionLost(self, reason):
        print("Lost connection with client.")
        
    def dataReceived(self, data):
        # Process inputs, get outputs.
        "As soon as any data is received, write it back."
        s = data.decode()
        if s == "fetchall":
            self.transport.write(str(fetchall()).encode())
        elif s[:6] == "create":
            split = s.split('|')
            if split[1] == "tournament":
                create_tournament(int(split[2]), split[3], int(split[4]))
                self.transport.write("Finished".encode())
            elif split[1] == "player":
                create_player(int(split[2]), split[3], int(split[4]))
                self.transport.write("Finished".encode())
        elif s[:6] == "delete":
            split = s.split('|')
            if split[1] == "tournament":
                delete_tournament(int(split[2]))
                self.transport.write("Finished".encode())
            elif split[1] == "player":
                delete_player(int(split[2]))
                self.transport.write("Finished".encode())
        else:
            # This means it will be a database instruction.
            cur = db.cursor()
            cur.execute(s)
            db.commit()
            # print("PROCESSED:", s)

def network_init():
    try:
        port_file = open("port.txt")
    except:
        port_file = open("port.txt", 'w')
        port_file.write(str(DEFAULT_PORT))
        port_file.close()
        port_file = open("port.txt")
        
    try:
        read_port = int(port_file.read())
        port_file.close()
    except ValueError:
        read_port = DEFAULT_PORT
        port_file.close()
        port_file = open("port.txt", 'w')
        port_file.write(str(DEFAULT_PORT))
        port_file.close()
        
    s = input(f"Input Port (Defualt {read_port}): ")
    global port
    
    if not s:
        port = read_port
    else:
        try:
            s_int = int(s)
        except ValueError:
            print("Invalid port entry.")
            quit()
        if s_int < 1024 or s_int > 65535:
            print("Invalid port entry.")
            quit()

        if s_int != read_port:
            save = (input("Would you like to save this port for next time? (y/n): ")).lower()[0] == 'y'
            if save:
                port_file = open("port.txt", 'w')
                port_file.write(str(s_int))
                port_file.close()
                print(f"Default port changed to {s_int}")
        port = s_int
            
if __name__ == "__main__":
    network_init()
    init() # Set up database if necessary.
    
    # This runs the protocol on specified port
    factory = protocol.ServerFactory() # Basic server factory.
    factory.protocol = SimpleServer
    
    reactor.listenTCP(port, factory)
    print(f"Listening on port {port}.")
    print("Ctrl + C to terminate.")
    reactor.run()
