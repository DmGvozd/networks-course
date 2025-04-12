import socket
import random
import sys
import threading
import os
import hashlib
import queue
import time

def read_file_chunks(filename, chunk_size):
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def calculate_checksum(data):
    return hashlib.md5(data).digest()

def send_file(sock, client_address, filename, chunk_size, ack_queue, stop_event):
    sequence_number = 0
    file_sent_successfully = False
    try:
        for chunk in read_file_chunks(filename, chunk_size):
            if stop_event.is_set():
                break
            checksum = calculate_checksum(chunk)
            packet = bytes([sequence_number]) + checksum + chunk
            while not stop_event.is_set():
                if random.random() > 0.3:
                    try:
                        sock.sendto(packet, client_address)
                        print(f"Sent packet {sequence_number}")
                    except OSError as e:
                        print(f"Socket error during send: {e}")
                        return
                try:
                    ack = ack_queue.get(timeout=1)
                    if ack == sequence_number:
                        print(f"Received ACK {sequence_number}")
                        break
                except queue.Empty:
                    print(f"Timeout on packet {sequence_number}, resending...")
            sequence_number = 1 - sequence_number
        file_sent_successfully = True
    finally:
        if file_sent_successfully:
            sock.sendto(b'EOF', client_address)
            print("File send complete.")
        else:
            print("File sending aborted.")

def handle_packets(sock, client_address, expected_sequence, ack_queue, output_file, stop_event):
    with open(output_file, 'wb') as f:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                if addr != client_address:
                    continue

                if data == b'EOF':
                    print("File received successfully from client.")
                    break

                if len(data) == 1:
                    ack_queue.put(data[0])
                    continue

                if len(data) < 17:
                    continue

                sequence_number = data[0]
                checksum = data[1:17]
                chunk = data[17:]

                if calculate_checksum(chunk) != checksum:
                    print(f"Checksum error on packet {sequence_number}, ignored")
                    continue

                if sequence_number == expected_sequence[0]:
                    f.write(chunk)
                    expected_sequence[0] = 1 - expected_sequence[0]

                if random.random() > 0.3:
                    ack = bytes([sequence_number])
                    sock.sendto(ack, addr)
                    print(f"Received packet {sequence_number}, sent ACK")

            except Exception as e:
                print(f"Receive error: {e}")
                break
        print("Server receiving finished.")

def main():
    server_address = ('127.0.0.1', 12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)

    try:
        filename_to_send = input("Enter filename to send to client: ")
        if not os.path.exists(filename_to_send):
            print("File not found.")
            sys.exit(1)

        chunk_size = 1024
        print("Server is running...")

        client_address = None
        expected_sequence = [0]
        stop_event = threading.Event()
        ack_queue = queue.Queue()

        while True:
            try:
                data, addr = sock.recvfrom(2048)
                if data == b'HELLO':
                    client_address = addr
                    print(f"Client connected from {client_address}")
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error waiting for client connection: {e}")
                stop_event.set()
                return

        handler_thread = threading.Thread(
            target=handle_packets,
            args=(sock, client_address, expected_sequence, ack_queue, 'received_from_client.txt', stop_event)
        )
        sender_thread = threading.Thread(
            target=send_file,
            args=(sock, client_address, filename_to_send, chunk_size, ack_queue, stop_event)
        )

        handler_thread.start()
        sender_thread.start()

        sender_thread.join()
        print("Server finished sending file.")

        handler_thread.join()
        print("Server finished receiving file.")

    except KeyboardInterrupt:
        print("\nServer interrupted.")
        stop_event.set()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
