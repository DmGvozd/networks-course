import sys
import socket

if len(sys.argv) != 4:
    print("Usage: python ports.py <IP> <start_port> <end_port>")
    sys.exit(1)

ip = sys.argv[1]

start_port = int(sys.argv[2])
end_port = int(sys.argv[3])

for port in range(start_port, end_port + 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    if s.connect_ex((ip, port)) != 0:
        print(port)
    s.close()
