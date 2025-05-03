import socket
import tkinter as tk
from tkinter import Canvas

HOST = '127.0.0.1'
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Waiting for a client to connect...")
conn, addr = server_socket.accept()
print(f"Client {addr} connected.")

root = tk.Tk()
root.title("Paint Server")
canvas = Canvas(root, width=400, height=400, bg="white")
canvas.pack()

last_x, last_y = None, None

def draw(x, y):
    global last_x, last_y
    if last_x is not None and last_y is not None:
        canvas.create_line(last_x, last_y, x, y, fill="black", width=2)
    last_x, last_y = x, y

try:
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("Client disconnected.")
                break
            parts = data.decode().strip().split(',')
            command = parts[0]
            if command == 'draw' and len(parts) >= 3:
                try:
                    x, y = int(parts[1]), int(parts[2])
                    draw(x, y)
                except ValueError:
                    print("Invalid coordinate format:", parts[1:3])
            elif command == 'reset':
                canvas.delete("all")
                last_x, last_y = None, None
            elif command == 'release':
                last_x, last_y = None, None
            else:
                print("Unknown command:", command)
        except Exception as e:
            print(f"Error receiving data: {e}")
        root.update_idletasks()
        root.update()
except KeyboardInterrupt:
    print("\nStopped by user.")
except Exception as e:
    print(f"Server error: {e}")
finally:
    conn.close()
    server_socket.close()
