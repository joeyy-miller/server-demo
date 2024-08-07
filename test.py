import unittest
import threading
import time
import socket
import argparse
from server import ChatServer
from client import ChatClient

class TestChatSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", type=int, default=12345, help="Port to run tests on")
        cls.args = parser.parse_args()

        # Start the server in a separate thread
        cls.server = ChatServer(port=cls.args.port, debug=True)
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Give the server time to start

    @classmethod
    def tearDownClass(cls):
        # Shutdown the server
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)

    def setUp(self):
        # Create a new client for each test
        self.client = ChatClient(port=self.args.port, debug=True)

    def tearDown(self):
        # Disconnect the client after each test
        if hasattr(self, 'client'):
            self.client.shutdown()

    def test_client_connection(self):
        # Test that a client can connect to the server
        self.client.start()
        self.assertTrue(self.client.running)

    def test_client_disconnection(self):
        # Test that a client can disconnect from the server
        self.client.start()
        self.client.shutdown()
        self.assertFalse(self.client.running)

    def test_server_broadcast(self):
        # Test that the server can broadcast messages
        test_message = "Test broadcast message"
        self.server.broadcast(test_message)
        time.sleep(0.1)  # Give time for the message to be processed
        self.assertIn(test_message, [m['message'] for m in self.server.chat_history])

    def test_client_send_message(self):
        # Test that a client can send a message
        self.client.start()
        test_message = "Test client message"
        self.client.client_socket.send(test_message.encode())
        time.sleep(0.1)  # Give time for the message to be processed
        self.assertIn(test_message, [m['message'] for m in self.server.chat_history])

    def test_whisper(self):
        # Test the whisper functionality
        client1 = ChatClient(port=self.args.port, debug=True)
        client2 = ChatClient(port=self.args.port, debug=True)
        client1.start()
        client2.start()
        client1.username = "User1"
        client2.username = "User2"
        
        whisper_message = "/whisper User2 Hello, this is a secret"
        client1.client_socket.send(whisper_message.encode())
        time.sleep(0.1)  # Give time for the message to be processed
        
        # Check if the whisper is in the server's chat history
        whisper_found = any("WHISPER" in m['username'] and "User1" in m['message'] and "User2" in m['message'] for m in self.server.chat_history)
        self.assertTrue(whisper_found)

    def test_user_list(self):
        # Test the user list functionality
        self.client.start()
        self.client.username = "TestUser"
        time.sleep(0.1)  # Give time for the user to be added to the server's client list
        
        self.assertIn("TestUser", [info["username"] for info in self.server.clients.values()])

    def test_kick_user(self):
        # Test the kick user functionality
        self.client.start()
        self.client.username = "TestUser"
        time.sleep(0.1)  # Give time for the user to be added to the server's client list
        
        self.server.kick_user("TestUser")
        time.sleep(0.1)  # Give time for the user to be kicked
        
        self.assertNotIn("TestUser", [info["username"] for info in self.server.clients.values()])

    def test_server_shutdown(self):
        # Test server shutdown
        temp_server = ChatServer(port=12347, debug=True)
        server_thread = threading.Thread(target=temp_server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)  # Give the server time to start

        temp_server.shutdown()
        time.sleep(1)  # Give the server time to shut down

        # Try to connect to the server, it should fail
        with self.assertRaises(ConnectionRefusedError):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 12347))

    def test_chat_history(self):
        # Test that chat history is maintained and limited
        self.server.max_history = 5
        for i in range(10):
            self.server.broadcast(f"Test message {i}")
        
        self.assertEqual(len(self.server.chat_history), 5)
        self.assertEqual(self.server.chat_history[-1]['message'], "SERVER: Test message 9")

if __name__ == '__main__':
    unittest.main()
