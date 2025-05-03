import socket
import struct
import time
import os
import sys

def checksum(data):
    if len(data) % 2 == 1:
        data += b'\x00'
    s = sum(struct.unpack('!' + 'H' * (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    return ~s & 0xFFFF

def create_icmp_packet(id, seq, data=b''):
    icmp_type = 8
    icmp_code = 0
    header = struct.pack('!BBHHH', icmp_type, icmp_code, 0, id, seq)
    packet = header + data
    chksum = checksum(packet)
    packet = struct.pack('!BBHHH', icmp_type, icmp_code, chksum, id, seq) + data
    return packet

def send_and_receive(dest_addr, ttl, timeout, id, seq):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        sock.settimeout(timeout)
        
        packet = create_icmp_packet(id, seq)
        start_time = time.time()
        try:
            sock.sendto(packet, (dest_addr, 0))
            data, address = sock.recvfrom(1024)
            end_time = time.time()
            rtt = (end_time - start_time) * 1000
            icmp_header = data[20:28]
            icmp_type, icmp_code, _, _, _ = struct.unpack('!BBHHH', icmp_header)
            return icmp_type, icmp_code, address[0], rtt
        except socket.timeout:
            return None, None, None, None
        finally:
            sock.close()
    except PermissionError:
        print("Permission denied: ICMP messages require admin privileges")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

def traceroute(dest_addr, max_hops=30, timeout=1, packets_per_hop=3):
    id = os.getpid() & 0xFFFF
    for ttl in range(1, max_hops + 1):
        line = f'{ttl}: '
        output = []
        reached = False
        for seq in range(1, packets_per_hop + 1):
            icmp_type, icmp_code, addr, rtt = send_and_receive(dest_addr, ttl, timeout, id, seq)
            if addr:
                try:
                    host_name = socket.gethostbyaddr(addr)[0]
                    output.append(f'{addr} ({host_name}) {rtt:.3f}ms')
                except socket.herror:
                    output.append(f'{addr} {rtt:.3f}ms')
                if addr == dest_addr:
                    reached = True
            else:
                output.append('*')
        print(line + ' '.join(output))
        if reached:
            break

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python3 traceroute.py <hostname> [packets_per_hop] [max_hops]")
        sys.exit(1)
        
    dest_input = sys.argv[1]
    try:
        dest_addr = socket.gethostbyname(dest_input)
    except socket.gaierror:
        print("Invalid hostname")
        sys.exit(1)
    
    packets_per_hop = 3
    max_hops = 30

    if len(sys.argv) >= 3:
        try:
            packets_per_hop = int(sys.argv[2])
        except ValueError:
            print("packets_per_hop must be an integer")
            sys.exit(1)
    if len(sys.argv) == 4:
        try:
            max_hops = int(sys.argv[3])
        except ValueError:
            print("max_hops must be an integer")
            sys.exit(1)

    try:
        traceroute(dest_addr, max_hops=max_hops, packets_per_hop=packets_per_hop)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
