import socket
import threading
import json
import time

BROADCAST_PORT = 5556
TCP_PORT = 5555

class ChessNetwork:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection = None
        self.is_server = False
        self.receive_callback = None
        self.running = False

        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.available_rooms = {}
        self.room_name = ""

    def start_server(self, room_name):
        self.is_server = True
        self.room_name = room_name
        try:
            self.socket.bind(('', TCP_PORT))
            self.socket.listen(1)
            self.running = True
            threading.Thread(target=self._accept_loop, daemon=True).start()
            threading.Thread(target=self._broadcast_presence, daemon=True).start()
            return True, "Waiting for connection..."
        except Exception as e:
            return False, str(e)

    def _broadcast_presence(self):
        while self.running and not self.connection:
            msg = json.dumps({"room": self.room_name}).encode('utf-8')
            try:
                self.broadcast_socket.sendto(msg, ('<broadcast>', BROADCAST_PORT))
            except:
                pass
            time.sleep(1)

    def start_discovery(self):
        self.running = True
        try:
            self.broadcast_socket.bind(('', BROADCAST_PORT))
        except:
            pass
        threading.Thread(target=self._discovery_loop, daemon=True).start()

    def _discovery_loop(self):
        while self.running and not self.connection:
            try:
                self.broadcast_socket.settimeout(2.0)
                data, addr = self.broadcast_socket.recvfrom(1024)
                info = json.loads(data.decode('utf-8'))
                self.available_rooms[addr[0]] = info["room"]
            except:
                pass

    def get_rooms(self):
        return self.available_rooms

    def _accept_loop(self):
        try:
            conn, addr = self.socket.accept()
            self.connection = conn
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
        except:
            pass

    def connect(self, ip):
        try:
            self.socket.connect((ip, TCP_PORT))
            self.connection = self.socket
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True, "Connected"
        except Exception as e:
            return False, str(e)

    def _receive_loop(self):
        while self.running and self.connection:
            try:
                data = self.connection.recv(1024)
                if not data:
                    break
                msg = data.decode('utf-8')
                if self.receive_callback:
                    self.receive_callback(msg)
            except:
                break
        self.close()

    def send_move(self, move_uci):
        if self.connection:
            try:
                self.connection.send(move_uci.encode('utf-8'))
            except:
                self.close()

    def close(self):
        self.running = False
        if self.connection and self.connection != self.socket:
            try:
                self.connection.close()
            except:
                pass
        try:
            self.socket.close()
        except:
            pass
        try:
            self.broadcast_socket.close()
        except:
            pass
        self.connection = None
