import socket
import random
import time
import datetime
import statistics

def udp_ping_server(host='127.0.0.1', port=12345):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"UDP Ping Server started on {host}:{port}")
    print("Simulating 20% packet loss")

    running = True
    try:
        while running:
            try:
                message, address = server_socket.recvfrom(1024)
                if random.random() <= 0.2:
                    print(f"Packet from {address} lost (simulated)")
                    continue

                modified_message = message.decode().upper()
                print(f"Received from {address}: {message.decode()}, replying: {modified_message}")
                server_socket.sendto(modified_message.encode(), address)
            except Exception as e:
                print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        print("\nUDP Ping Server shutting down...")
        running = False
    finally:
        server_socket.close()
        print("UDP Ping Server closed.")


if __name__ == '__main__':
    udp_ping_server()
