import socket
import time
import random
import os
import sys
import threading
import hashlib
import queue

def read_file_chunks(filename, chunk_size):
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def calculate_checksum(data):
    return hashlib.md5(data).digest()

def send_file(sock, server_address, filename, chunk_size):
    sequence_number = 0
    file_sent_successfully = False
    try:
        for chunk in read_file_chunks(filename, chunk_size):
            checksum = calculate_checksum(chunk)
            packet = bytes([sequence_number]) + checksum + chunk
            while True:
                if random.random() > 0.3:
                    try:
                        sock.sendto(packet, server_address)
                        print(f"Sent packet {sequence_number}")
                    except OSError as e:
                        print(f"Socket error during send: {e}")
                        return
                try:
                    ack, _ = sock.recvfrom(1024)
                    if ack[0] == sequence_number:
                        print(f"Received ACK {ack[0]}")
                        break
                except socket.timeout:
                    print(f"Timeout on packet {sequence_number}, resending...")
                except Exception as e:
                    print(f"Error receiving ACK: {e}")
                    return
            sequence_number = 1 - sequence_number
        file_sent_successfully = True
    finally:
        if file_sent_successfully:
            sock.sendto(b'EOF', server_address)
            print("File send complete.")
        else:
            print("File sending aborted.")

def receive_file(sock, stop_event, filename="received_from_server.txt"):
    print("Receiver started")
    expected_sequence = 0
    with open(filename, 'wb') as f:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                print(f"Got data: {len(data)} bytes from {addr}")

                if data == b'EOF':
                    print("File received successfully from server.")
                    break

                if len(data) < 17:
                    continue

                sequence_number = data[0]
                checksum = data[1:17]
                chunk = data[17:]

                if calculate_checksum(chunk) != checksum:
                    print(f"Checksum error on packet {sequence_number}, ignored")
                    continue

                print(f"Expected: {expected_sequence}, Got: {sequence_number}")
                if sequence_number == expected_sequence:
                    f.write(chunk)
                    f.flush()
                    print(f"Written {len(chunk)} bytes to file.")
                    expected_sequence = 1 - expected_sequence
                else:
                    print(f"Unexpected packet {sequence_number}, expected {expected_sequence}")

                if random.random() > 0.3:
                    ack = bytes([sequence_number])
                    sock.sendto(ack, addr)
                    print(f"Sent ACK for packet {sequence_number}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receive error: {e}")
                break
        print("Client receiving finished.")

def main():
    server_address = ('127.0.0.1', 12345)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        timeout = float(input("Enter timeout in seconds: "))
        chunk_size = int(input("Enter chunk size in bytes: "))
        client_socket.settimeout(timeout)

        send_file_path = input("Enter filename to send to server (leave blank to skip): ").strip()

        client_socket.sendto(b'HELLO', server_address)
        print("Sent HELLO to server")

        stop_event = threading.Event()

        receive_thread = threading.Thread(target=receive_file, args=(client_socket, stop_event))
        receive_thread.start()

        if send_file_path:
            if not os.path.exists(send_file_path):
                print("File not found.")
                return
            time.sleep(1)
            send_file(client_socket, server_address, send_file_path, chunk_size)

        print("Waiting for file transfers to complete...")
        receive_thread.join()


    except KeyboardInterrupt:
        print("\nClient interrupted.")
        stop_event.set()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
