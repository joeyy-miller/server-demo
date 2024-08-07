import socket
import threading
import signal
import sys
import json
import time
import os
import argparse

'''
Client.py - A simple chat client that connects to a chat server and sends/receives messages.
This client uses a separate thread to receive messages from the server.
Commands:
- /quit: Disconnect from the server and exit the client.
- /help: Display a list of available commands.
-

The client can be stopped by sending a SIGINT signal (Ctrl+C).
'''

class ChatClient:
    def __init__(self, host='127.0.0.1', port=12344, debug=False):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.username = ""
        self.debug = debug
        self.help_menu = """
Available commands:
/help               - Display this help menu
/whisper <username> <message>
                    - Send a private message to a specific user
/users              - Request a list of online users from the server
/clear              - Clear the screen
quit                - Exit the chat

Chat tips:
- Messages you send will appear after your username prompt.
- Received messages will appear above your current input line.
- Different types of messages are color-coded for easy identification.
"""

    def log(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    def start(self):
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Unable to connect to the server. Make sure it's running.")
            return

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.username = input("Enter your username: ")
        self.client_socket.send(self.username.encode())

        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

        self.clear_screen()
        print("Welcome to the chat!")
        print("Type '/help' for a list of commands.")
        while self.running:
            try:
                message = input(f"{self.username} > ")
                if message.lower() == 'quit':
                    self.shutdown()
                elif message.lower() == '/help':
                    self.display_help_menu()
                elif message.lower() == '/clear':
                    self.clear_screen()
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
                data = self.client_socket.recv(1024).decode()
                if data:
                    self.log(f"Raw data received: {data}")
                    self.print_message(data)
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

    def print_message(self, message, color='\033[0m'):
        print(f"\r{color}{message}\033[0m")
        print(f"{self.username} > ", end="", flush=True)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_help_menu(self):
        self.print_message(self.help_menu, color='\033[92m')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat Client")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    client = ChatClient(debug=args.debug)
    client.start()