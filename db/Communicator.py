import socket

class Communicator:
    # SOCKET MUST BE SET UP BEFORE SENDING TO COMMUNICATOR.
    def __init__(self, sock):
        self.__sock = sock

    def send_msg(self, message):
        self.__sock.sendall(message.encode()) # Send entire message.

    def recv_msg(self):
        total_data = []
        
        while True:
            chunk = self.__sock.recv(1024)
            if not chunk:
                break
            total_data.append(chunk)
        
        return ''.join(total_data)
