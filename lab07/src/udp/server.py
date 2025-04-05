import socket
import time

def udp_heartbeat_server(host='127.0.0.1', port=12345, client_timeout=5):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"UDP Heartbeat Server started on {host}:{port}")
    print(f"Client timeout set to {client_timeout} seconds")

    clients_data = {}
    server_socket.settimeout(1.0)

    running = True
    try:
        while running:
            current_time = time.time()

            timed_out_clients = []
            for client_id, data in clients_data.items():
                if current_time - data['last_seen'] > client_timeout:
                    timed_out_clients.append(client_id)

            for client_id in timed_out_clients:
                print(f"Client {client_id} at {clients_data[client_id]['address']} timed out. Last seen at {time.ctime(clients_data[client_id]['last_seen'])}")
                del clients_data[client_id]

            try:
                message, address = server_socket.recvfrom(1024)
                received_time = time.time()
                msg_str = message.decode()
                client_id, seq_str, ts_str = msg_str.split(',')
                sequence_number = int(seq_str)
                timestamp = float(ts_str)

                if client_id not in clients_data:
                    print(f"New client connected: {client_id} from {address}")
                    clients_data[client_id] = {'last_seen': received_time, 'last_seq': sequence_number -1, 'address': address}

                data = clients_data[client_id]
                expected_seq = data['last_seq'] + 1
                if sequence_number > expected_seq:
                    lost_count = sequence_number - expected_seq
                    print(f"[Client {client_id}] Packet loss detected: {lost_count} packet(s) lost. "
                          f"Expected seq={expected_seq}, got={sequence_number}")

                print(f"Heartbeat received from {client_id} at {address}: seq={sequence_number}")
                data['last_seen'] = received_time
                data['last_seq'] = sequence_number

            except socket.timeout:
                pass
            except ValueError:
                print(f"Received malformed packet from {address}: {message.decode()}")
            except Exception as e:
                print(f"An error occurred: {e}")

    except KeyboardInterrupt:
        print("\nUDP Heartbeat Server shutting down...")
        running = False
    finally:
        server_socket.close()
        print("UDP Heartbeat Server closed.")


if __name__ == '__main__':
    udp_heartbeat_server()
