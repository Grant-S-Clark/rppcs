import socket # ????

if __name__ == "__main__":
    # create an INET STREAMING socket.
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # bind the socket to a public host with the port 8000.
    serversocket.bind((socket.gethostname(), 8000))
    
    serversocket.listen(1) # only allow one connection (the master program)
