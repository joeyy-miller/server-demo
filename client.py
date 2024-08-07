import socket
import threading
import signal
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def start(self):
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Unable to connect to the server. Make sure it's running.")
            return

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        username = input("Enter your username: ")
        self.client_socket.send(username.encode())

        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

        while self.running:
            try:
                message = input()
                if message.lower() == 'quit':
                    self.shutdown()
                else:
                    self.client_socket.send(message.encode())
            except EOFError:
                self.shutdown()

    def signal_handler(self, signum, frame):
        print("\nReceived shutdown signal. Disconnecting...")
        self.shutdown()

    def shutdown(self):
        self.running = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.client_socket.close()
        print("Disconnected from server.")
        sys.exit(0)

    def receive_messages(self):
        while self.running:
            try:
                self.client_socket.settimeout(1.0)
                message = self.client_socket.recv(1024).decode()
                if message:
                    print(message)
                else:
                    print("Lost connection to the server.")
                    self.shutdown()
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    print("Lost connection to the server.")
                    self.shutdown()
                break

if __name__ == "__main__":
    client = ChatClient()
    client.start()
