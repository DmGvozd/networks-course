import socket

UDP_IP = ""
UDP_PORT = 28070

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Клиент UDP слушает на {UDP_PORT}")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"Получено от {addr}: {data.decode('utf-8')}")
