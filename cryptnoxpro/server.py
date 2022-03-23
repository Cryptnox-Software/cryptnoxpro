import socket
import threading
import ctypes
import pickle
from . import config
import cryptnoxpy

HEADER = 64
PORT = 5051
SERVER = socket.gethostbyname(socket.gethostname() + ".local")
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

class server_thread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def send(self,client,msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)


    def handle_client(self,conn,addr):
        print(f'\nNew connection {addr} connected')
        try:
            config._REMOTE_CONNECTIONS.append(conn)
        except Exception as e:
            print(f'Exception in client handling sub_thread: {e}')


    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id


    def run(self):
            server.listen()
            print(f'\n[Listening] Server is listening on {SERVER}')
            connections = []
            threads = []
            while True:
                try:
                    conn, addr = server.accept()
                    print(f'Conn:{conn} Addr:{addr}')
                    connections.append(conn)
                    if addr[0] != '95.216.215.183':
                        print('Found new connection, assigning thread now.')
                        thread = threading.Thread(target=self.handle_client,args=(conn,addr))
                        thread.start()
                        threads.append(thread)
                        print(f'\nActive connections: {threading.activeCount() - 1}')
                    else:
                        print('Found exit thread, closing server now')
                        raise
                except (KeyboardInterrupt,Exception) as e:
                    for each in connections:
                        print('\nClosing connections')
                        each.close()
                    for each in threads:
                        print('\nJoining sub-threads')
                        each.join()
                    server.shutdown(socket.SHUT_RDWR)
                    server.close()
                    print('\nServer is closed')
                    break