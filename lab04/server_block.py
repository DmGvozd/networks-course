import socket
import sys
import threading
import os
import hashlib
import json
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
CACHE_DIR = 'server_cache'
BLOCKLIST_FILE = 'block.json'

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def log_event(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {event}\n")
        log.flush()

def log_request(client_addr, method, target_host, target_path, status_code, status_message=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = client_addr[0] if client_addr else "unknown"
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {client_ip} - {method} http://{target_host}{target_path} - {status_code} {status_message}\n")
        log.flush()

def get_cache_filename(key):
    hashed = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, hashed)

def parse_http_response(response_bytes):
    parts = response_bytes.split(b"\r\n\r\n", 1)
    header_text = parts[0].decode('iso-8859-1', errors='replace')
    headers = {}
    for line in header_text.split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return header_text, headers

def load_blocklist():
    if os.path.exists(BLOCKLIST_FILE):
        with open(BLOCKLIST_FILE, "r") as f:
            data = json.load(f)
        return [domain.lower() for domain in data.get("blocked", [])]
    return []

BLOCKLIST = load_blocklist()

def handle_client(client_socket, client_addr):
    target_host = ""
    target_path = ""
    method = ""
    try:
        request_data = client_socket.recv(4096)
        if not request_data:
            client_socket.close()
            return
        request_text = request_data.decode('iso-8859-1', errors='replace')
        request_lines = request_text.split("\r\n")
        if len(request_lines) == 0:
            client_socket.close()
            return
        req_line = request_lines[0].split()
        if len(req_line) < 3:
            client_socket.close()
            return
        method, full_path, protocol = req_line
        if full_path.startswith("http://"):
            full_path = full_path[len("http://"):]
        elif full_path.startswith("https://"):
            full_path = full_path[len("https://"):]
        if full_path.startswith("/"):
            full_path = full_path[1:]
        if "/" in full_path:
            target_host, target_path = full_path.split("/", 1)
            target_path = "/" + target_path
        else:
            target_host = full_path
            target_path = "/"

        # Check if the target host is in the blocklist
        if target_host.lower() in BLOCKLIST:
            response_text = "This page is blocked."
            response_body = response_text.encode('iso-8859-1')
            response = f"HTTP/1.1 403 Forbidden\r\nContent-Length: {len(response_body)}\r\nConnection: close\r\n\r\n".encode('iso-8859-1') + response_body
            log_request(client_addr, method, target_host, target_path, "403", "Forbidden")
            client_socket.sendall(response)
            client_socket.close()
            return

        headers = {}
        content_length = 0
        header_ended = False
        for line in request_lines[1:]:
            if line == "":
                header_ended = True
                continue
            if not header_ended:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    if key.lower() == "host":
                        continue
                    if key.lower() == "content-length":
                        try:
                            content_length = int(value)
                        except:
                            content_length = 0
                    headers[key] = value
        body = b""
        if method.upper() == "POST" and content_length > 0:
            remaining = request_data.split(b"\r\n\r\n", 1)[1]
            while len(remaining) < content_length:
                remaining += client_socket.recv(4096)
            body = remaining[:content_length]
        use_cache = (method.upper() == "GET")
        cache_key = f"{target_host}{target_path}"
        cache_file = get_cache_filename(cache_key)
        cond_headers = {}
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    cached_response = f.read()
                _, cached_headers = parse_http_response(cached_response)
                if "Last-Modified" in cached_headers:
                    cond_headers["If-Modified-Since"] = cached_headers["Last-Modified"]
                if "ETag" in cached_headers:
                    cond_headers["If-None-Match"] = cached_headers["ETag"]
            except Exception:
                cond_headers = {}
        new_request = f"{method} {target_path} HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n"
        if use_cache and cond_headers:
            for key, value in cond_headers.items():
                new_request += f"{key}: {value}\r\n"
        for key, value in headers.items():
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
            client_socket.sendall(response)
            client_socket.close()
            return
        finally:
            target_socket.close()
        status_code = "000"
        status_message = ""
        try:
            status_line = response.split(b"\r\n", 1)[0].decode('iso-8859-1', errors='replace')
            parts = status_line.split()
            if len(parts) >= 2:
                status_code = parts[1]
                status_message = " ".join(parts[2:]) if len(parts) > 2 else ""
        except Exception:
            pass
        if use_cache and os.path.exists(cache_file):
            if status_code == "304":
                try:
                    with open(cache_file, "rb") as f:
                        response = f.read()
                    log_request(client_addr, method, target_host, target_path, "304", "Not Modified")
                except Exception:
                    pass
            elif status_code == "200":
                try:
                    with open(cache_file, "wb") as f:
                        f.write(response)
                except Exception:
                    pass
                log_request(client_addr, method, target_host, target_path, status_code, status_message)
            else:
                log_request(client_addr, method, target_host, target_path, status_code, status_message)
        elif use_cache and not os.path.exists(cache_file):
            if status_code == "200":
                try:
                    with open(cache_file, "wb") as f:
                        f.write(response)
                except Exception:
                    pass
            log_request(client_addr, method, target_host, target_path, status_code, status_message)
        else:
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
