import socket
import threading
import time
from tkinter import *

class UDPServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Получатель UDP")
        self.root.geometry("300x300")

        Label(root, text="Введите IP:").pack()
        self.ip_entry = Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        Label(root, text="Порт для получения:").pack()
        self.port_entry = Entry(root)
        self.port_entry.insert(0, "12345")
        self.port_entry.pack()

        Label(root, text="Скорость передачи:").pack()
        self.speed_value = StringVar(value="0 KB/s")
        Label(root, textvariable=self.speed_value).pack()

        Label(root, text="Число полученных пакетов:").pack()
        self.packets_value = StringVar(value="0/0")
        Label(root, textvariable=self.packets_value).pack()

        Label(root, text="Потерянные пакеты:").pack()
        self.lost_value = StringVar(value="0")
        Label(root, textvariable=self.lost_value).pack()

        self.start_button = Button(root, text="Получить", command=self.start_server_thread)
        self.start_button.pack(pady=10)

        self.running = False
        self.reset_stats()

    def reset_stats(self):
        self.total_packets = 0
        self.received_packets = 0
        self.total_data = 0
        self.start_time = None

    def start_server_thread(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((ip, port))
        print("UDP Server listening...")

        self.reset_stats()

        while self.running:
            try:
                data, addr = server_socket.recvfrom(65535)
                if self.start_time is None:
                    self.start_time = time.time()

                message = data.decode(errors='ignore')

                if message.startswith("#TOTAL="):
                    try:
                        self.total_packets = int(message.split("=")[1])
                    except:
                        continue
                else:
                    try:
                        timestamp, hex_data = message.split(":", 1)
                        packet_data = bytes.fromhex(hex_data)
                        self.total_data += len(packet_data)
                        self.received_packets += 1

                        elapsed = time.time() - self.start_time
                        speed_kb = (self.total_data / 1024) / elapsed if elapsed > 0 else 0
                        self.speed_value.set(f"{speed_kb:.2f} KB/s")
                        self.packets_value.set(f"{self.received_packets}/{self.total_packets}")
                        lost = self.total_packets - self.received_packets
                        self.lost_value.set(str(max(0, lost)))
                    except Exception as e:
                        print("Ошибка обработки пакета:", e)
            except Exception as e:
                print("Ошибка сервера:", e)

    def stop_server(self):
        self.running = False

if __name__ == "__main__":
    root = Tk()
    app = UDPServer(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_server)
    root.mainloop()
