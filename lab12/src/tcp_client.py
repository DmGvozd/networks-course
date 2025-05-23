import socket
import random
import time
import threading
from tkinter import *

class TCPClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Отправитель TCP")
        self.root.geometry("300x280")

        Label(root, text="Введите IP адрес получателя:").pack()
        self.ip_entry = Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        Label(root, text="Выберите порт отправки:").pack()
        self.port_entry = Entry(root)
        self.port_entry.insert(0, "12345")
        self.port_entry.pack()

        Label(root, text="Введите количество пакетов для отправки:").pack()
        self.packets_entry = Entry(root)
        self.packets_entry.insert(0, "100")
        self.packets_entry.pack()

        self.send_button = Button(root, text="Отправить", command=self.send_data_thread)
        self.send_button.pack(pady=10)

    def send_data_thread(self):
        threading.Thread(target=self.send_data, daemon=True).start()

    def send_data(self):
        try:
            packets_to_send = int(self.packets_entry.get())
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.ip_entry.get(), int(self.port_entry.get())))

            client_socket.sendall(f"#TOTAL={packets_to_send}\n".encode())

            for i in range(packets_to_send):
                data = random.randbytes(1024)
                timestamp = time.time()
                message = f"{timestamp}:{data.hex()}\n"
                client_socket.sendall(message.encode())
                time.sleep(0.01)

            client_socket.close()
        except Exception as e:
            print("Error sending data:", e)

if __name__ == "__main__":
    root = Tk()
    app = TCPClient(root)
    root.mainloop()
