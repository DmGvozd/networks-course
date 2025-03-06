import socket
import sys

if len(sys.argv) != 4:
    print(f"Usage: python3 {sys.argv[0]} <server_host> <server_port> <filename>")
    sys.exit(1)

server_host = sys.argv[1]

try:
    server_port = int(sys.argv[2])
except ValueError:
    print("Error: server_port must be an integer.")
    sys.exit(1)

filename = sys.argv[3]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((server_host, server_port))
except socket.gaierror:
    print(f"Error: Unable to resolve host '{server_host}'. Please check the server address.")
    sys.exit(1)
except ConnectionRefusedError:
    print(f"Error: Connection refused. Please check if the server is running at {server_host}:{server_port}.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error occurred: {e}")
    sys.exit(1)

request_line = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
client_socket.send(request_line.encode())

response = b""
try:
    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        response += data
except Exception as e:
    print(f"Error while receiving data: {e}")
    sys.exit(1)
finally:
    client_socket.close()

print(response.decode())
