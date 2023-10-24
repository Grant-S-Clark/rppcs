import socket
from Communicator import Communicator

PORT = 8000

if __name__ == "__main__":
    # create an INET STREAMING socket.
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # bind the socket to a public host with the defined PORT value.
    hostname = socket.gethostname()
    serversocket.bind((hostname, PORT))

    # Print the hostname and port for the user.
    print(f"LISTENING ON {(hostname, PORT)}")
    
    serversocket.listen(1) # only allow one connection at a time (the master program)

    connection, address = serversocket.accept() # Client program has connected
    print(f"CLIENT CONNECTED.")
    
    comm = Communicator(serversocket)

    try:
        client_msg = comm.recv_msg()
    except OSError:
        print("CLIENT SOCKET CLOSED.")
        serversocket.shutdown()
        serversocket.close()
        quit()
        
    print(f"RECIEVED: \"{client_msg}\"")

    comm.send_msg("Message Recieved.")

    serversocket.shutdown()
    serversocket.close()
    
    
