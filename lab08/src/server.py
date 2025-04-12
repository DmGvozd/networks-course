import socket
import random
import sys
import os

def main():
    server_address = ('127.0.0.1', 12345)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)

    output_filename = "received.txt"
    expected_sequence = 0
    client_address = None

    print("Server listening...")
    try:
        with open(output_filename, 'wb') as f:
            while True:
                try:
                    data, current_client_address = server_socket.recvfrom(2048)

                    if client_address is None:
                        client_address = current_client_address

                    if current_client_address != client_address:
                        continue

                    if data == b'EOF':
                        print("File received successfully from client.")
                        break

                    if len(data) < 1:
                         continue

                    sequence_number = data[0]
                    chunk = data[1:]

                    if sequence_number == expected_sequence:
                        f.write(chunk)
                        expected_sequence = 1 - expected_sequence
                        print(f"Received expected packet {sequence_number}. Bytes written.")
                    else:
                        print(f"Received unexpected packet {sequence_number}, expected {expected_sequence}. Ignoring.")

                    if random.random() > 0.3:
                        ack_packet = bytes([sequence_number])
                        server_socket.sendto(ack_packet, client_address)
                        print(f"Sent ACK for {sequence_number}")
                    else:
                        print(f"ACK for {sequence_number} lost (simulated)")

                except socket.timeout:
                    continue
                except OSError as e:
                    print(f"Socket error: {e}")
                    break
                except Exception as e:
                    print(f"Receive error: {e}")
                    break

    except FileNotFoundError:
        print(f"Error creating output file: {output_filename}")
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()
        print("Server socket closed.")

if __name__ == "__main__":
    main()
