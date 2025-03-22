import socket
import time
import datetime

BROADCAST_IP = '255.255.255.255'
UDP_PORT = 28070

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print(f"Сервер UDP рассылает время на {BROADCAST_IP}:{UDP_PORT}")

while True:
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Текущее время сервера: {current_time}"
    sock.sendto(message.encode('utf-8'), (BROADCAST_IP, UDP_PORT))
    print(f"Отправлено: {message}")
    time.sleep(1)
