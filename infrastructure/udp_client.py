import socket
import threading
import time

from app.config import PS5_IP, HANDSHAKE_PORT, TELEMETRY_PORT


class GT7UdpClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", TELEMETRY_PORT))

        self._running = False
        self._handshake_thread = None

    # ======================
    # HANDSHAKE
    # ======================
    def _handshake_loop(self):
        message = b"A\x00\x00\x00"

        while self._running:
            try:
                self.sock.sendto(message, (PS5_IP, HANDSHAKE_PORT))
            except OSError as e:
                print("Handshake error:", e)

            time.sleep(1)

    # ======================
    # CONTROLE
    # ======================
    def start(self):
        """
        Inicia handshake e permite recepção de dados
        """
        if self._running:
            return

        self._running = True

        self._handshake_thread = threading.Thread(
            target=self._handshake_loop,
            daemon=True
        )
        self._handshake_thread.start()

    def stop(self):
        self._running = False
        try:
            self.sock.close()
        except OSError:
            pass

    # ======================
    # RECEPÇÃO
    # ======================
    def receive(self, buffer_size: int = 4096):
        """
        Bloqueante.
        Retorna (data, addr)
        """
        return self.sock.recvfrom(buffer_size)
