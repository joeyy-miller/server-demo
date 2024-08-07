import socket
import requests
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from ftplib import FTP
import paramiko

# 1. Basic TCP Client
def tcp_client():
    host = 'example.com'
    port = 80
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
        response = s.recv(4096)
    
    print("TCP Client Response:", response.decode())

# 2. Basic UDP Client
def udp_client():
    host = 'example.com'
    port = 53
    message = b'Hello, UDP Server!'
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(message, (host, port))
        data, server = s.recvfrom(4096)
    
    print("UDP Client Response:", data.decode())

# 3. HTTP GET Request using requests library
def http_get():
    response = requests.get('https://api.github.com/events')
    print("HTTP GET Status Code:", response.status_code)
    print("HTTP GET Content:", response.json()[:2])

# 4. HTTP POST Request using requests library
def http_post():
    data = {'key': 'value'}
    response = requests.post('https://httpbin.org/post', data=data)
    print("HTTP POST Status Code:", response.status_code)
    print("HTTP POST Content:", response.json())

# 5. Asynchronous HTTP requests
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def async_http():
    urls = ['http://example.com', 'http://example.org', 'http://example.net']
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        responses = await asyncio.gather(*tasks)
    
    for url, response in zip(urls, responses):
        print(f"Async HTTP Response from {url}: {response[:50]}...")

# 6. Email sending using SMTP
def send_email():
    sender = 'sender@example.com'
    receiver = 'receiver@example.com'
    password = 'your_password'
    
    msg = MIMEText('This is a test email sent from Python.')
    msg['Subject'] = 'Test Email'
    msg['From'] = sender
    msg['To'] = receiver
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
    
    print("Email sent successfully")

# 7. FTP file transfer
def ftp_transfer():
    ftp = FTP('ftp.example.com')
    ftp.login(user='username', passwd='password')
    
    with open('local_file.txt', 'rb') as file:
        ftp.storbinary('STOR remote_file.txt', file)
    
    ftp.quit()
    print("File transferred successfully via FTP")

# 8. SSH connection and command execution
def ssh_command():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('example.com', username='user', password='password')
    
    stdin, stdout, stderr = client.exec_command('ls -l')
    print("SSH Command Output:", stdout.read().decode())
    
    client.close()

def print_menu():
    print("\nPython Networking Examples:")
    print("1. TCP Client")
    print("2. UDP Client")
    print("3. HTTP GET Request")
    print("4. HTTP POST Request")
    print("5. Asynchronous HTTP Requests")
    print("6. Email Sending (requires configuration)")
    print("7. FTP Transfer (requires configuration)")
    print("8. SSH Command Execution (requires configuration)")
    print("0. Exit")
    
# Main function to run all examples
def main():
    while True:
        print_menu()
        choice = input("Enter the number of the example you want to run (0 to exit): ")
        
        if choice == '0':
            print("Exiting the program. Goodbye!")
            break
        elif choice == '1':
            print("\nRunning TCP Client Example")
            tcp_client()
        elif choice == '2':
            print("\nRunning UDP Client Example")
            udp_client()
        elif choice == '3':
            print("\nRunning HTTP GET Request")
            http_get()
        elif choice == '4':
            print("\nRunning HTTP POST Request")
            http_post()
        elif choice == '5':
            print("\nRunning Asynchronous HTTP Requests")
            asyncio.run(async_http())
        elif choice == '6':
            print("\nEmail Sending Example")
            print("This example requires configuration. Please edit the send_email() function with your credentials.")
            confirm = input("Do you want to proceed? (y/n): ")
            if confirm.lower() == 'y':
                send_email()
        elif choice == '7':
            print("\nFTP Transfer Example")
            print("This example requires configuration. Please edit the ftp_transfer() function with your credentials.")
            confirm = input("Do you want to proceed? (y/n): ")
            if confirm.lower() == 'y':
                ftp_transfer()
        elif choice == '8':
            print("\nSSH Command Execution Example")
            print("This example requires configuration. Please edit the ssh_command() function with your credentials.")
            confirm = input("Do you want to proceed? (y/n): ")
            if confirm.lower() == 'y':
                ssh_command()
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()