import socket
import sys
import os
import threading

if len(sys.argv) != 3:
    print(f"Usage: python3 {sys.argv[0]} <server_port> <concurrency_level>")
    sys.exit(1)

try:
    server_port = int(sys.argv[1])
    concurrency_level = int(sys.argv[2])
except ValueError:
    print("Error: server_port and concurrency_level must be integers.")
    sys.exit(1)

thread_semaphore = threading.Semaphore(concurrency_level)

def handle_client(connection_socket):
    with thread_semaphore:
        try:
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

        except Exception as e:
            print(f"Error handling request: {e}")

        finally:
            connection_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind(('', server_port))
    server_socket.listen(5)
except Exception as e:
    print(f"Socket error: {e}")
    sys.exit(1)

print(f"Server running on port {server_port} with concurrency level {concurrency_level}.")

try:
    while True:
        connection_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(connection_socket,))
        client_thread.start()

except KeyboardInterrupt:
    print("\nServer stopped by user.")

finally:
    server_socket.close()
