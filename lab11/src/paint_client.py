import socket
import tkinter as tk
from tkinter import Canvas

HOST = '127.0.0.1'
PORT = 12345

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
except Exception as e:
    print(f"Could not connect to the server: {e}")
    exit(1)

root = tk.Tk()
root.title("Paint Client")
canvas = Canvas(root, width=400, height=400, bg="white")
canvas.pack()

last_x, last_y = None, None

def send_draw(x, y):
    try:
        message = f"draw,{x},{y}"
        client_socket.send(message.encode())
    except Exception as e:
        print(f"Error sending draw command: {e}")

def send_reset():
    try:
        client_socket.send("reset".encode())
    except Exception as e:
        print(f"Error sending reset command: {e}")
    canvas.delete("all")
    
def send_release():
    try:
        client_socket.send("release".encode())
    except Exception as e:
        print(f"Error sending release command: {e}")

def on_press(event):
    global last_x, last_y
    last_x, last_y = event.x, event.y

def on_drag(event):
    global last_x, last_y
    if last_x is not None and last_y is not None:
        canvas.create_line(last_x, last_y, event.x, event.y, fill="black", width=2)
        send_draw(event.x, event.y)
    last_x, last_y = event.x, event.y

def on_release(event):
    global last_x, last_y
    last_x, last_y = None, None
    send_release()

canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

button = tk.Button(root, text="Clear", command=send_reset)
button.pack()

try:
    root.mainloop()
except KeyboardInterrupt:
    print("\nInterrupted by user.")
finally:
    try:
        client_socket.close()
    except Exception:
        pass
