import socket
import time

def udp_heartbeat_client(server_host='127.0.0.1', server_port=12345, interval=1):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_host, server_port)
    sequence_number = 0
    client_id = f"Client_{socket.gethostname()}_{int(time.time() * 1000) % 10000}"
    print(f"Heartbeat Client [{client_id}] started. Sending to {server_host}:{server_port} every {interval}s")

    running = True
    try:
        while running:
            sequence_number += 1
            current_time = time.time()
            message = f"{client_id},{sequence_number},{current_time:.6f}"
            try:
                client_socket.sendto(message.encode(), server_address)
                print(f"Sent heartbeat: seq={sequence_number}, time={current_time:.6f}")
            except Exception as e:
                print(f"Error sending data: {e}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\nHeartbeat Client [{client_id}] shutting down...")
        running = False
    finally:
        client_socket.close()
        print(f"Heartbeat Client [{client_id}] closed.")


if __name__ == '__main__':
    udp_heartbeat_client()
