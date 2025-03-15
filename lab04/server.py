import socket
import sys
import threading
from datetime import datetime

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} <port>")
    sys.exit(1)
try:
    PORT = int(sys.argv[1])
except ValueError:
    print("Error: port must be an integer.")
    sys.exit(1)

HOST = 'localhost'
LOG_FILE = 'server_logs.log'

def log_event(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {event}\n")
        log.flush()

def log_request(client_addr, method, target_host, target_path, status_code, status_message=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = client_addr[0] if client_addr else "unknown"
    status_message = status_message if status_message else ""
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {client_ip} - {method} http://{target_host}{target_path} - {status_code} {status_message}\n")
        log.flush()

def handle_client(client_socket, client_addr):
    target_host = ""
    target_path = ""
    method = ""
    try:
        request_data = client_socket.recv(4096)
        if not request_data:
            return
        request_text = request_data.decode('iso-8859-1')
        request_lines = request_text.split("\r\n")
        if not request_lines:
            return
        req_line = request_lines[0].split()
        if len(req_line) < 3:
            return
        method, full_path, protocol = req_line
        if full_path.startswith("/"):
            full_path = full_path[1:]
        if "/" in full_path:
            target_host, target_path = full_path.split("/", 1)
            target_path = "/" + target_path
        else:
            target_host = full_path
            target_path = "/"
        headers = {}
        content_length = 0
        for line in request_lines[1:]:
            if line == "":
                break
            if line.lower().startswith("host:"):
                continue
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":")[1].strip())
            headers[line.split(":")[0].strip()] = line.split(":")[1].strip()
        body = b""
        if method == "POST" and content_length > 0:
            remaining_data = request_data[len(request_text):]
            if len(remaining_data) < content_length:
                remaining_data += client_socket.recv(content_length - len(remaining_data))
            body = remaining_data[:content_length]
        new_request = f"{method} {target_path} HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n"
        for key, value in headers.items():
            if key.lower() != "host":
                new_request += f"{key}: {value}\r\n"
        new_request += "\r\n"
        if body:
            new_request = new_request.encode('iso-8859-1') + body
        else:
            new_request = new_request.encode('iso-8859-1')
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.settimeout(5)
        try:
            target_socket.connect((target_host, 80))
            target_socket.sendall(new_request)
            response = b""
            while True:
                chunk = target_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
        except Exception as e:
            response = f"HTTP/1.1 502 Bad Gateway\r\n\r\nProxy Error: {str(e)}".encode('iso-8859-1')
            log_request(client_addr, method, target_host, target_path, "502", "Bad Gateway")
        finally:
            target_socket.close()
        status_code = "000"
        status_message = ""
        try:
            status_line = response.split(b"\r\n", 1)[0].decode('iso-8859-1')
            status_code = status_line.split()[1]
            status_message = " ".join(status_line.split()[2:])
        except:
            pass
        log_request(client_addr, method, target_host, target_path, status_code, status_message)
        client_socket.sendall(response)
    except Exception as e:
        error_response = f"HTTP/1.1 500 Internal Server Error\r\n\r\nProxy Error: {str(e)}".encode('iso-8859-1')
        client_socket.sendall(error_response)
        log_request(client_addr, method, target_host, target_path, "500", "Internal Server Error")
    finally:
        client_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_socket.bind((HOST, PORT))
except Exception as e:
    print(f"Error binding to {HOST}:{PORT} - {e}")
    log_event(f"Error binding to {HOST}:{PORT} - {e}")
    sys.exit(1)
server_socket.listen(5)
log_event(f"Server started on {HOST}:{PORT}")
print(f"Proxy server listening on {HOST}:{PORT}")

while True:
    try:
        client, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client, addr)).start()
    except KeyboardInterrupt:
        log_event("Server shutting down")
        print("\nServer shutting down")
        server_socket.close()
        sys.exit(0)
