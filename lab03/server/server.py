import socket
import sys
import os

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} <server_port>")
    sys.exit(1)

server_port = int(sys.argv[1])
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', server_port))
server_socket.listen(1)

print(f'Server running on port {server_port}')

try:
    while True:
        connection_socket, addr = server_socket.accept()
        request = connection_socket.recv(1024).decode()
        lines = request.split('\r\n')

        if len(lines) > 0 and len(lines[0].split()) >= 2:
            filename = lines[0].split()[1][1:]
        else:
            filename = ''

        if filename == '':
            filename = 'index.html'

        if os.path.isfile(filename):
            with open(filename, 'rb') as file:
                content = file.read()
            header = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
            connection_socket.send(header.encode() + content)
        else:
            header = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n'
            content = '<h1>404 Not Found</h1>'.encode()
            connection_socket.send(header.encode() + content)

        connection_socket.close()

except KeyboardInterrupt:
    print("\nServer stopped by user")

finally:
    server_socket.close()
