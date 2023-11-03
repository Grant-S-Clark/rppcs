# pip install --user twisted
from twisted.internet import protocol, reactor
import sqlite3

PORT = 8000
db = None # Will be set later.

# Translate all tables into a dictionary of 2 dimensional lists.
"""
ret["TT"] = [T]ournament [T]able dictionary
ret["MT"] = [M]atch [T]able dictionary
ret["GT"] = [G]ame [T]able dictionary
ret["PT"] = [P]layer [T]able dictionary
ret["BT"] = match [B]inary [T]ree table dictionary

ret["TT"][id] = [ name, date ]
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

class SimpleServer(protocol.Protocol):
    def connectionMade(self):
        print("Client has connected to the server.")

    def connectionLost(self, reason):
        print ("Lost connection with client.")
        
    def dataReceived(self, data):
        # Process inputs, get outputs.
        "As soon as any data is received, write it back."
        self.transport.write(str(fetchall()).encode())

def create_debug_testing_data():
    global db

    cur = db.cursor()

    # CREATE TEST TOURNEMENT
    cur.execute("INSERT INTO tournaments (id, name, date) VALUES (?, ?, DATE('now'))",
                (0, "TestTournament0")) # Values in a tuple
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
          
def create_test_tournament(t_id : int, players : int):
    """
    global db

    cur = db.cursor()

    # CREATE TEST TOURNEMENT
    cur.execute("INSERT INTO tournaments (id, name, date) VALUES (?, ?, DATE('now'))",
                (t_id, f"TestTournament{t_id}")) # Values in a tuple
    db.commit()

    # CREATE TEST PLAYERS
    for i in range(players):
        cur.execute(f"INSERT INTO players (id, name, skill) VALUES (?, ?, 0)",
                    (i, f"TestPlayer{i}"))
        db.commit()
    """
    # CREATE TEST MATCHES
    t = players
    num_matches = players % 2
    while t > 0:
        t //= 2;
        num_matches += t
        if t > 1:
            num_matches += t % 2

    print(num_matches)
    quit()

def init():
    global db
    db = sqlite3.connect("rppcs_data.db")
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    db.commit()
    
    # Tournament table
    cur.execute("""CREATE TABLE IF NOT EXISTS tournaments(id     INT UNSIGNED NOT NULL PRIMARY KEY,
                                                          name   TEXT NOT NULL,
                                                          date   DATE NOT NULL)""")

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
                                                      FOREIGN KEY (t_id) REFERENCES tournaments(id),
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
    
    
if __name__ == "__main__":
    init() # Set up database if necessary.
    create_debug_testing_data()
    
    # This runs the protocol on port 8000
    factory = protocol.ServerFactory() # Basic server factory.
    factory.protocol = SimpleServer
    reactor.listenTCP(PORT, factory)
    reactor.run()

