import socket
import threading

class ChessNetwork:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection = None
        self.is_server = False
        self.receive_callback = None
        self.running = False

    def start_server(self, port=5555):
        self.is_server = True
        try:
            self.socket.bind(('', port))
            self.socket.listen(1)
            threading.Thread(target=self._accept_loop, daemon=True).start()
            return True, "Waiting for connection..."
        except Exception as e:
            return False, str(e)

    def _accept_loop(self):
        try:
            conn, addr = self.socket.accept()
            self.connection = conn
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
        except:
            pass

    def connect(self, ip, port=5555):
        try:
            self.socket.connect((ip, port))
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
        self.connection = None
