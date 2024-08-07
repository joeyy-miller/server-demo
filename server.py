import socket
import threading
import queue
import signal
import sys
import json
import time
import argparse

'''
server.py - A simple chat server that allows clients to connect and send/receive messages.

This server uses a thread to handle each client connection, allowing multiple clients to connect at once.
The server also uses a queue to manage messages between the main server thread and the client threads.
All messages are broadcast to all connected clients.
Commands:
- /kick [username]: Kick a user from the server.
- /list: List all connected users.
- /help: Display a list of available commands.
- /quit: Shut down the server.
-

The server can be stopped by sending a SIGINT signal (Ctrl+C).
'''


class ChatServer:
    def __init__(self, host='127.0.0.1', port=12344, debug=False):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}
        self.message_queue = queue.Queue()
        self.running = True
        self.chat_history = []
        self.max_history = 50
        self.debug = debug
        self.commands = {
            '/help': self.cmd_help,
            '/users': self.cmd_users,
            '/kick': self.cmd_kick,
        }
        self.help_menu = """
Available server commands:
/help               - Display this help menu
/users              - List all connected users
/kick <username>    - Kick a user from the server
quit                - Shut down the server

Note: Regular messages will be broadcast to all users.
"""

    def log(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    def create_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def is_port_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, self.port))
            except OSError:
                return True
        return False

    def start(self):
        if self.is_port_in_use():
            print(f"Error: Port {self.port} is already in use.")
            print("Please choose a different port or wait a moment and try again.")
            sys.exit(1)

        self.create_socket()

        try:
            self.server_socket.bind((self.host, self.port))
        except OSError as e:
            print(f"Error binding to port {self.port}: {e}")
            print("Please try again in a few moments or choose a different port.")
            sys.exit(1)

        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        threading.Thread(target=self.accept_connections, daemon=True).start()
        threading.Thread(target=self.process_messages, daemon=True).start()

        print("Server commands: Type '/help' for a list of commands.")
        while self.running:
            try:
                message = input("Server > ")
                if message.lower() == 'quit':
                    self.shutdown()
                elif message.startswith('/'):
                    self.handle_server_command(message)
                else:
                    self.broadcast(message)
            except EOFError:
                self.shutdown()

    # ... (rest of the methods remain the same)

    def free_port(self):
        for conn in psutil.net_connections():
            if conn.laddr.port == self.port:
                try:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    self.log(f"Terminated process {conn.pid} using port {self.port}")
                except psutil.NoSuchProcess:
                    pass
                
    def signal_handler(self, signum, frame):
        print("\nReceived shutdown signal. Closing server...")
        self.shutdown()

    def shutdown(self):
        self.running = False
        self.broadcast("Server is shutting down.")
        for client_socket in list(self.clients.keys()):
            self.remove_client(client_socket)
        if self.server_socket:
            self.server_socket.close()
        print("Server shut down successfully.")
        sys.exit(0)

    def accept_connections(self):
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, addr = self.server_socket.accept()
                self.log(f"New connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def handle_client(self, client_socket, addr):
        try:
            username = client_socket.recv(1024).decode().strip()
            self.clients[client_socket] = {"username": username, "addr": addr}
            join_message = f"{username} has joined the chat!"
            self.broadcast(join_message)
            
            # Log the join event in the server console
            print(f"\r{join_message}")
            print("Server > ", end="", flush=True)
            
            # Add join event to chat history
            self.chat_history.append({"username": "SERVER", "message": join_message, "timestamp": time.time()})
            if len(self.chat_history) > self.max_history:
                self.chat_history.pop(0)
            
            self.send_chat_history(client_socket)

            while self.running:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                if message.startswith('/'):
                    self.handle_client_command(client_socket, message)
                else:
                    self.message_queue.put((username, f"{username}: {message}"))
        except (ConnectionResetError, OSError):
            pass
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        client_info = self.clients.pop(client_socket, None)
        if client_info:
            username = client_info["username"]
            leave_message = f"{username} has left the chat."
            self.broadcast(leave_message)
            
            # Log the leave event in the server console
            print(f"\r{leave_message}")
            print("Server > ", end="", flush=True)
            
            # Add leave event to chat history
            self.chat_history.append({"username": "SERVER", "message": leave_message, "timestamp": time.time()})
            if len(self.chat_history) > self.max_history:
                self.chat_history.pop(0)
        
        try:
            client_socket.close()
        except OSError:
            pass

    def broadcast(self, message):
        if not message.startswith("SERVER:"):
            message = f"SERVER: {message}"
        self.message_queue.put(("SERVER", message))

    def process_messages(self):
        while self.running:
            try:
                username, message = self.message_queue.get(timeout=1.0)
                self.log(f"Processing message: {message}")
                print(f"{message}")
                self.chat_history.append({"username": username, "message": message, "timestamp": time.time()})
                if len(self.chat_history) > self.max_history:
                    self.chat_history.pop(0)
                for client in list(self.clients.keys()):
                    try:
                        client.send(message.encode())
                    except:
                        self.remove_client(client)
            except queue.Empty:
                continue

    def send_chat_history(self, client_socket):
        for item in self.chat_history:
            client_socket.send(f"{item['message']}".encode())

    def handle_server_command(self, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            print(f"Unknown command: {cmd}")
            print("Type '/help' for a list of available commands.")

    def handle_client_command(self, client_socket, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == '/whisper' and len(args) >= 2:
            target_username = args[0]
            message = ' '.join(args[1:])
            self.whisper(client_socket, target_username, message)
        elif cmd == '/users':
            self.send_user_list(client_socket)
        elif cmd == '/help':
            self.send_help(client_socket)
        else:
            client_socket.send("Error: Unknown command".encode())

    def cmd_help(self, args):
        print(self.help_menu)

    def cmd_users(self, args):
        users = [info["username"] for info in self.clients.values()]
        print("Connected users: " + ", ".join(users))

    def cmd_kick(self, args):
        if not args:
            print("Usage: /kick <username>")
            return
        username = args[0]
        self.kick_user(username)

    def kick_user(self, username):
        for client, info in list(self.clients.items()):
            if info["username"] == username:
                client.send("You have been kicked from the server.".encode())
                self.remove_client(client)
                print(f"Kicked user: {username}")
                self.broadcast(f"{username} has been kicked from the chat.")
                return
        print(f"User {username} not found.")

    def whisper(self, sender_socket, target_username, message):
        sender_username = self.clients[sender_socket]["username"]
        for client, info in self.clients.items():
            if info["username"] == target_username:
                whisper_message = f"[Whisper from {sender_username} to {target_username}]: {message}"
                client.send(f"[Whisper from {sender_username}]: {message}".encode())
                sender_socket.send(f"[Whisper to {target_username}]: {message}".encode())
                
                # Log the whisper in the server console
                print(f"\r{whisper_message}")
                print("Server > ", end="", flush=True)
                
                # Add whisper to chat history
                self.chat_history.append({"username": "WHISPER", "message": whisper_message, "timestamp": time.time()})
                if len(self.chat_history) > self.max_history:
                    self.chat_history.pop(0)
                
                return
        sender_socket.send(f"Error: User {target_username} not found".encode())

    def send_user_list(self, client_socket):
        user_list = [info["username"] for info in self.clients.values()]
        client_socket.send(f"Online users: {', '.join(user_list)}".encode())

    def send_help(self, client_socket):
        help_message = """
Available commands:
/whisper <username> <message> - Send a private message
/users - See a list of online users
/help - Display this help message
"""
        client_socket.send(help_message.encode())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat Server")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-p", "--port", type=int, default=12345, help="Port to run the server on")
    args = parser.parse_args()

    server = ChatServer(port=args.port, debug=args.debug)
    server.start()