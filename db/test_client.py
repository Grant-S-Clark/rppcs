import socket
from Communicator import Communicator

if __name__ == "__main__":
    address = input("ADDRESS: ")
    port = int(input("PORT: "))

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    clientsocket.connect((address, port))

    comm = Communicator(clientsocket)

    comm.send_msg("Hello World!")
    reply = comm.recv_msg()

    print(f"REPLY RECIEVED: \"{reply}\"")
    
    clientsocket.shutdown()
    clientsocket.close()
