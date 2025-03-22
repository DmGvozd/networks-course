import socket

HOST = '127.0.0.1'
PORT = 8888

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    while True:
        command = input("Введите команду ('exit' для выхода): ")
        if command.lower() == 'exit':
            break

        s.sendall(command.encode())
        data = s.recv(4096)
        print(f"Ответ сервера:\n{data.decode()}")
