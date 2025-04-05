import socket
import time

def udp_ping_client_b(host='127.0.0.1', port=12345, count=10, timeout=1.0):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    server_address = (host, port)
    print(f"Pinging {host}:{port} with {count} requests:")

    try:
        for i in range(1, count + 1):
            sequence_number = i
            send_time_sec = time.time()
            message = f"Ping {sequence_number} {send_time_sec:.6f}"

            try:
                client_socket.sendto(message.encode(), server_address)
                send_time = time.monotonic()

                response, _ = client_socket.recvfrom(1024)
                receive_time = time.monotonic()
                rtt = (receive_time - send_time)
                print(f"Reply from {host}: seq={sequence_number}, RTT={rtt:.6f}s, data: {response.decode()}")

            except socket.timeout:
                print(f"Request timed out for seq={sequence_number}")
            except Exception as e:
                print(f"An error occurred: {e}")

            if i < count:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nPing client interrupted.")
    finally:
        client_socket.close()
        print("Ping client closed.")


if __name__ == '__main__':
    udp_ping_client_b()
