import socket
import random
import time
import threading
from tkinter import *

class UDPClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Отправитель UDP")
        self.root.geometry("300x350")

        Label(root, text="Введите IP адрес получателя:").pack()
        self.ip_entry = Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        Label(root, text="Выберите порт отправки:").pack()
        self.port_entry = Entry(root)
        self.port_entry.insert(0, "12345")
        self.port_entry.pack()

        Label(root, text="Введите количество пакетов:").pack()
        self.packets_entry = Entry(root)
        self.packets_entry.insert(0, "100")
        self.packets_entry.pack()

        Label(root, text="Размер одного пакета (в байтах):").pack()
        self.packet_size_entry = Entry(root)
        self.packet_size_entry.insert(0, "1024")
        self.packet_size_entry.pack()

        self.send_button = Button(root, text="Отправить", command=self.send_data_thread)
        self.send_button.pack(pady=10)

    def send_data_thread(self):
        threading.Thread(target=self.send_data, daemon=True).start()

    def send_data(self):
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
            total_packets = int(self.packets_entry.get())
            packet_size = int(self.packet_size_entry.get())

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            client_socket.sendto(f"#TOTAL={total_packets}".encode(), (ip, port))

            for i in range(total_packets):
                data = random.randbytes(packet_size)
                timestamp = time.time()
                message = f"{timestamp}:{data.hex()}"
                client_socket.sendto(message.encode(), (ip, port))
                time.sleep(0.01)

            client_socket.close()
        except Exception as e:
            print("Ошибка при отправке данных:", e)

if __name__ == "__main__":
    root = Tk()
    app = UDPClient(root)
    root.mainloop()
