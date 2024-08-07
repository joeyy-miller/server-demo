# Server Demo

This is a simple chat system implemented in Python, consisting of a server and client application. It allows multiple users to connect and chat in real-time, with features like private messaging (whispers) and user management.

## Features

- Multi-user chat room
- Private messaging (whispers)
- User join/leave notifications
- Server-side user management (kick users)
- Chat history
- Debug mode for troubleshooting

## How It Works

The system uses socket programming to establish connections between the server and clients. Here's a brief overview:

1. The server starts and listens for incoming connections.
2. Clients connect to the server and provide a username.
3. Messages sent by clients are broadcast to all connected users.
4. Special commands (starting with '/') provide additional functionality.

## Usage

### Starting the Server
python server.py [-d]
Copy
Use the `-d` flag to run in debug mode.

### Starting a Client
python client.py [-d]
Copy
Use the `-d` flag to run in debug mode.

### Available Commands

- `/whisper <username> <message>`: Send a private message
- `/users`: List all connected users
- `/help`: Display available commands

Server-only commands:
- `/kick <username>`: Kick a user from the server

## Running Tests

To run the test suite:
python -m unittest test_chat_system.py
Copy
## Known Issues and Limitations

1. The system doesn't handle server crashes gracefully. Clients may need to be manually restarted.
2. There's no user authentication, so users can potentially use duplicate usernames.
3. The chat history is stored in memory and is lost when the server restarts.
4. Large numbers of concurrent users may impact performance (not load-tested).
5. The system doesn't support file transfers or multimedia messages.
6. There's no encryption for messages, so it's not suitable for sensitive communications.

## Future Improvements

- Implement user authentication
- Add persistent storage for chat history
- Improve error handling and recovery mechanisms
- Implement message encryption
- Add support for file transfers and multimedia messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
