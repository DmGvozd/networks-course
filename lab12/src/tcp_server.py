import socket
import threading
import time
from tkinter import *

class TCPServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Получатель TCP")
        self.root.geometry("300x280")

        Label(root, text="Введите IP:").pack()
        self.ip_entry = Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        Label(root, text="Выберите порт для получения:").pack()
        self.port_entry = Entry(root)
        self.port_entry.insert(0, "12345")
        self.port_entry.pack()

        Label(root, text="Скорость передачи:").pack()
        self.speed_value = StringVar(value="0 B/s")
        Label(root, textvariable=self.speed_value).pack()

        Label(root, text="Число полученных пакетов:").pack()
        self.packets_value = StringVar(value="0/0")
        Label(root, textvariable=self.packets_value).pack()

        self.start_button = Button(root, text="Получить", command=self.start_server_thread)
        self.start_button.pack(pady=10)

        self.server_socket = None
        self.running = False

        self.reset_stats()

    def reset_stats(self):
        self.packets_received = 0
        self.total_packets = 0
        self.total_data = 0
        self.start_time = None

    def start_server_thread(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip_entry.get(), int(self.port_entry.get())))
        self.server_socket.listen(1)
        print("Server is listening...")

        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            self.reset_stats()
            self.start_time = time.time()
            self.handle_client(client_socket)

    def handle_client(self, client_socket):
        buffer = b""
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line_str = line.decode(errors='ignore')
                    if self.start_time is None:
                        self.start_time = time.time()
                    if line_str.startswith("#TOTAL="):
                        try:
                            self.total_packets = int(line_str.split("=")[1])
                            self.packets_value.set(f"{self.packets_received}/{self.total_packets}")
                        except:
                            pass
                        continue

                    try:
                        timestamp, hex_data = line_str.split(":", 1)
                        data_bytes = bytes.fromhex(hex_data)
                        self.total_data += len(data_bytes)
                        self.packets_received += 1
                        elapsed = time.time() - self.start_time
                        speed_b = self.total_data / elapsed if elapsed > 0 else 0
                        self.speed_value.set(f"{speed_b:.2f} B/s")
                        self.packets_value.set(f"{self.packets_received}/{self.total_packets}")
                    except Exception as e:
                        print("Parse error:", e)
        except Exception as e:
            print("Connection error:", e)
        finally:
            client_socket.close()

    def stop_server(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    root = Tk()
    app = TCPServer(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_server)
    root.mainloop()
