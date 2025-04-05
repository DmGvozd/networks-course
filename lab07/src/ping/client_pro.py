import socket
import time
import statistics

def udp_ping_client_c(host='127.0.0.1', port=12345, count=10, timeout=1.0):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    server_address = (host, port)
    print(f"Pinging {host}:{port} with {count} requests:")

    rtts = []
    packets_sent = 0
    packets_received = 0

    try:
        for i in range(1, count + 1):
            sequence_number = i
            send_time_sec = time.time()
            message = f"Ping {sequence_number} {send_time_sec:.6f}"
            packets_sent += 1

            try:
                client_socket.sendto(message.encode(), server_address)
                send_time = time.monotonic()

                response, _ = client_socket.recvfrom(1024)
                receive_time = time.monotonic()
                rtt = (receive_time - send_time)
                rtts.append(rtt)
                packets_received += 1
                print(f"Reply from {host}: seq={sequence_number}, time={rtt * 1000:.3f}ms")

            except socket.timeout:
                print(f"Request timed out for seq={sequence_number}")
            except Exception as e:
                print(f"An error occurred: {e}")

            if i < count:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nPing client interrupted.")
    finally:
        client_socket.close()
        print(f"\n--- {host} ping statistics ---")
        print(f"{packets_sent} packets transmitted, {packets_received} packets received, ", end="")
        loss = 0.0
        if packets_sent > 0:
            loss = ((packets_sent - packets_received) / packets_sent) * 100
        print(f"{loss:.1f}% packet loss")

        if rtts:
            min_rtt = min(rtts) * 1000
            max_rtt = max(rtts) * 1000
            avg_rtt = statistics.mean(rtts) * 1000
            print(f"rtt min/avg/max = {min_rtt:.3f}/{avg_rtt:.3f}/{max_rtt:.3f} ms")
        print("Ping client closed.")


if __name__ == '__main__':
    udp_ping_client_c()
