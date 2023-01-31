import pickle
import selectors
import types
import socket

import cryptnoxpy

from .command import Command

try:
    import enums
except ImportError:
    from .. import enums


class Server(Command):
    _name = enums.Command.SERVER.value
    _HEADER_SIZE = 64
    _ENCODING = 'utf-8'

    def _execute(self, card: cryptnoxpy) -> int:
        self.sel = selectors.DefaultSelector()
        self.card = card
        self._start(self.data.host, self.data.port)

        return 0

    def _start(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen()
        print(f"Listening on {(host, port)}")
        sock.setblocking(False)
        self.sel.register(sock, selectors.EVENT_READ, data=None)

        try:
            self._loop()
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()

    def _loop(self):
        while True:
            events = self.sel.select(timeout=0.1)
            self._process_events(events)

    def _process_events(self, events):
        for key, mask in events:
            if key.data is None:
                self._accept_wrapper(key.fileobj)
            else:
                self._service_connection(key, mask)

    def _accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def _service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            data.outb += self._receive(sock, data.addr)

        if mask & selectors.EVENT_WRITE and data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

    def _close(self, sock, address):
        print(f"Closing connection to {address}")
        self.sel.unregister(sock)
        sock.close()

    def _receive(self, sock, address) -> bytes:
        print(f'Receiving command')
        message = sock.recv(Server._HEADER_SIZE)
        if not message:
            self._close(sock, address)

        try:
            message_length = int(message.decode(Server._ENCODING))
        except ValueError:
            return b''

        pickled_data = sock.recv(message_length)
        if not pickled_data:
            self._close(sock, address)
            return b''

        return self._process_in_card(pickled_data)

    def _process_in_card(self, pickled_data: str) -> bytes:
        print(f'Transmitting APDU command to card')
        try:
            command = pickle.loads(pickled_data)
        except pickle.UnpicklingError:
            return b''

        try:
            response = self.card.connection._reader.send(command)
        except cryptnoxpy.CryptnoxException as error:
            print(f'Error with card: {error}')
            return b''

        print(f'Responding back to server')
        pickled_response = pickle.dumps(response)
        msg_length = len(pickled_response)
        send_length = str(msg_length).encode(Server._ENCODING)
        send_length += (' ' * (Server._HEADER_SIZE - len(send_length))).encode(Server._ENCODING)

        return send_length + pickled_response
