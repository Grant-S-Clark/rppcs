# pip install --user twisted
from twisted.internet import protocol, reactor
import sqlite3

PORT = 8000
db = None # Will be set later.

# Translate all tables into a dictionary of 2 dimensional lists.
"""
ret["TT"] = tournament table list
ret["MT"] = match table list
ret["GT"] = game table list
ret["PT"] = player table list
ret["BT"] = match binary tree table list
"""
def fetchall():
    global db
    cur = db.cursor()
    
    ret = dict()

    cur.execute("SELECT * FROM tournaments")
    ret["TT"] = list()
    for row in cur:
        ret["PT"].append(list(row))

    cur.execute("SELECT * FROM matches")
    ret["MT"] = list()
    for row in cur:
        ret["PT"].append(list(row))

    cur.execute("SELECT * FROM games")
    ret["GT"] = list()
    for row in cur:
        ret["PT"].append(list(row))
    
    cur.execute("SELECT * FROM players")
    ret["PT"] = list()
    for row in cur:
        ret["PT"].append(list(row))

    cur.execute("SELECT * FROM match_tree")
    ret["BT"] = list()
    for row in cur:
        ret["PT"].append(list(row))
    
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

def init():
    global db
    db = sqlite3.connect("rppcs_data.db")
    cur = db.cursor()
    # Tournament table
    cur.execute("""CREATE TABLE IF NOT EXISTS tournaments(id     INT UNSIGNED NOT NULL,
                                                          name   TEXT NOT NULL,
                                                          date   DATE NOT NULL)""")

    # Match table
    cur.execute("""CREATE TABLE IF NOT EXISTS matches(id      INT UNSIGNED NOT NULL,
                                                      t_id    INT UNSIGNED NOT NULL,
                                                      p1_id   INT UNSIGNED NOT NULL,
                                                      p2_id   INT UNSIGNED NOT NULL)""")

    # Game table
    cur.execute("""CREATE TABLE IF NOT EXISTS games(id         INT UNSIGNED NOT NULL,
                                                    m_id       INT UNSIGNED NOT NULL,
                                                    p1_score   TINYINT UNSIGNED NOT NULL,
                                                    p2_score   TINYINT UNSIGNED NOT NULL)""")

    # Player table
    cur.execute("""CREATE TABLE IF NOT EXISTS players(id      INT UNSIGNED,
                                                      name    TEXT NOT NULL,
                                                      skill   SMALLINT UNSIGNED NOT NULL)""")

    # Match binary tree
    cur.execute("""CREATE TABLE IF NOT EXISTS match_tree(parent_id      INT UNSIGNED NOT NULL,
                                                         l_child_id     INT UNSIGNED NOT NULL,
                                                         r_child_id     INT UNSIGNED NOT NULL)""")
    db.commit()
    
    # Insert the null player into the players table if necessary.
    # Null player will have an id of 0.
    res = cur.execute("SELECT * FROM players WHERE id = 0")
    if res.fetchone() is None:
        cur.execute("INSERT INTO players (id, name, skill) VALUES (0, 'N/A', 0)")
        
    db.commit()
    
    
if __name__ == "__main__":
    init() # Set up database if necessary.
    
    # This runs the protocol on port 8000
    factory = protocol.ServerFactory() # Basic server factory.
    factory.protocol = SimpleServer
    reactor.listenTCP(PORT, factory)
    reactor.run()

