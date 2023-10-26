from twisted.internet import protocol, reactor

PORT = 8000
# a client protocol

class SimpleClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        self.transport.write(b"hello, world!")

    def dataReceived(self, data):
        # As soon as any data is received, print it and close connection.
        print("Server said:", data.decode())
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print(f"connection lost")


class SimpleFactory(protocol.ClientFactory):
    protocol = SimpleClient

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed!")
        print(reason)
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        reactor.stop()

# this only runs if the module was *not* imported
if __name__ == "__main__":
    f = SimpleFactory()
    reactor.connectTCP("localhost", PORT, f)
    reactor.run()
