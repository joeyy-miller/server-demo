import socket
import threading
import queue
import signal
import sys

class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.message_queue = queue.Queue()
        self.running = True

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        threading.Thread(target=self.accept_connections, daemon=True).start()
        threading.Thread(target=self.process_messages, daemon=True).start()

        while self.running:
            try:
                message = input()
                if message.lower() == 'quit':
                    self.shutdown()
                else:
                    self.broadcast(f"SERVER: {message}")
            except EOFError:
                self.shutdown()

    def signal_handler(self, signum, frame):
        print("\nReceived shutdown signal. Closing server...")
        self.shutdown()

    def shutdown(self):
        self.running = False
        self.broadcast("SERVER: Server is shutting down.")
        for client_socket in list(self.clients.keys()):
            self.remove_client(client_socket)
        self.server_socket.close()
        print("Server shut down successfully.")
        sys.exit(0)

    def accept_connections(self):
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def handle_client(self, client_socket, addr):
        try:
            username = client_socket.recv(1024).decode().strip()
            self.clients[client_socket] = username
            self.broadcast(f"{username} has joined the chat!")

            while self.running:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                self.message_queue.put((username, message))
        except (ConnectionResetError, OSError):
            pass
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        username = self.clients.pop(client_socket, None)
        if username:
            self.broadcast(f"{username} has left the chat.")
        try:
            client_socket.close()
        except OSError:
            pass

    def broadcast(self, message):
        self.message_queue.put(("SERVER", message))

    def process_messages(self):
        while self.running:
            try:
                username, message = self.message_queue.get(timeout=1.0)
                print(f"{username}: {message}")
                for client in list(self.clients.keys()):
                    try:
                        client.send(f"{username}: {message}".encode())
                    except:
                        self.remove_client(client)
            except queue.Empty:
                continue

if __name__ == "__main__":
    server = ChatServer()
    server.start()
