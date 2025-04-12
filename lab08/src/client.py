import socket
import time
import random
import os
import sys

def read_file_chunks(filename, chunk_size):
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def main():
    server_address = ('127.0.0.1', 12345)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        timeout = float(input("Enter timeout in seconds: "))
        chunk_size = int(input("Enter chunk size in bytes: "))
        client_socket.settimeout(timeout)
        filename = input("Enter filename to send: ")
        
        if not os.path.exists(filename):
            print("File not found.")
            sys.exit(1)

        sequence_number = 0

        for chunk in read_file_chunks(filename, chunk_size):
            packet = bytes([sequence_number]) + chunk
            while True:
                if random.random() > 0.3:
                    try:
                        client_socket.sendto(packet, server_address)
                    except OSError as e:
                        print(f"Socket error during send: {e}")
                        sys.exit(1)
                print(f"Sent packet {sequence_number}")
                try:
                    ack, _ = client_socket.recvfrom(1024)
                    if ack[0] == sequence_number:
                        print(f"Received ACK {ack[0]}")
                        break
                except socket.timeout:
                    print(f"Timeout on packet {sequence_number}, resending...")
                except Exception as e:
                    print(f"Error receiving ACK: {e}")
                    break
            sequence_number = 1 - sequence_number

        try:
            client_socket.sendto(b'EOF', server_address)
            print("Sent EOF marker.")
            print("File transfer completed.")
        except OSError as e:
            print(f"Socket error sending EOF: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
