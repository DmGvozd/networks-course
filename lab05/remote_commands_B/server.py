import socket
import subprocess
import platform

HOST = '127.0.0.1'
PORT = 8888

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

print(f"Сервер слушает на {HOST}:{PORT}")

while True:
    conn, addr = s.accept()
    print(f"Подключено клиентом: {addr}")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            command_str = data.decode().strip()
            print(f"Получена команда: {command_str}")

            try:
                if command_str.lower() == 'calc':
                    process = subprocess.Popen(['open', '-a', 'Calculator'])
                    result = "Калькулятор запущен."
                elif command_str.lower() == 'textedit':
                    process = subprocess.Popen(['open', '-a', 'TextEdit'])
                    result = "TextEdit запущен."
                else:
                    command_parts = command_str.split()

                    if command_parts[0].lower() == 'ping':
                        if platform.system() == "Windows":
                            command_parts.insert(1, '/n')
                            command_parts.insert(2, '4')
                        else:
                            command_parts.insert(1, '-c')
                            command_parts.insert(2, '4')


                    process = subprocess.Popen(command_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()
                    result = stdout + stderr
                    if not result:
                        result = f"Команда выполнена, но вывод пуст. Код возврата: {process.returncode}"

            except FileNotFoundError:
                result = "Ошибка: Команда не найдена."
            except Exception as e:
                result = f"Произошла ошибка: {e}"

            conn.sendall(result.encode())
