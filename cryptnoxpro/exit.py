import socket
from smartcard.System import readers
from smartcard.util import toHexString
import pickle
import json


HEADER = 64
PORT = 5051
SERVER = '95.216.215.183'
ADDR = (SERVER, PORT)

def initiate_exit():
    print('Initiating server exit')
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
