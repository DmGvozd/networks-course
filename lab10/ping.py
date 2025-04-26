import socket
import struct
import time
import select
import statistics
import sys
import os
import errno
import signal

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_DEST_UNREACH = 3
ICMP_TIME_EXCEEDED = 11

ICMP_UNREACH_CODES = {
    0: "Network unreachable",
    1: "Host unreachable",
    2: "Protocol unreachable",
    3: "Port unreachable",
    4: "Fragmentation needed",
    5: "Source route failed",
    6: "Destination network unknown",
    7: "Destination host unknown",
    8: "Source host isolated",
    9: "Network administratively prohibited",
    10: "Host administratively prohibited",
    11: "Network unreachable for TOS",
    12: "Host unreachable for TOS",
    13: "Communication administratively prohibited"
}

def checksum(source_string):
    sum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2
    if countTo < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_packet(id, sequence):
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, id, sequence)
    data = struct.pack('!d', time.time())
    checksum_val = checksum(header + data)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, checksum_val, id, sequence)
    return header + data

def parse_icmp_packet(packet):
    if len(packet) < 28:
        return None, None, None, None
    ip_header = packet[:20]
    icmp_header = packet[20:28]
    icmp_type, code, checksum_recv, p_id, sequence = struct.unpack('!BBHHH', icmp_header)
    return icmp_type, code, p_id, sequence

def print_stats(host, packets_sent, packets_received, rtts):
    print(f"\n--- {host} ping statistics ---")
    print(f"{packets_sent} packets transmitted, {packets_received} packets received, ", end="")
    loss = ((packets_sent - packets_received) / packets_sent) * 100 if packets_sent else 0
    print(f"{loss:.1f}% packet loss")
    if rtts:
        min_rtt = min(rtts)
        avg_rtt = statistics.mean(rtts)
        max_rtt = max(rtts)
        if len(rtts) > 1:
            stdev = statistics.stdev(rtts)
            print(f"rtt min/avg/max/mdev = {min_rtt:.2f}/{avg_rtt:.2f}/{max_rtt:.2f}/{stdev:.2f} ms")
        else:
            print(f"rtt min/avg/max = {min_rtt:.2f}/{avg_rtt:.2f}/{max_rtt:.2f} ms")

def ping(host, count=4, timeout=1):
    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Cannot resolve {host}: Unknown host")
        return

    print(f"PING {host} ({dest_addr}) with {count} ICMP packets:")

    rtts = []
    packets_sent = 0
    packets_received = 0

    def signal_handler(sig, frame):
        print_stats(host, packets_sent, packets_received, rtts)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.settimeout(timeout)
            pid = os.getpid() & 0xFFFF

            for sequence in range(1, count + 1):
                try:
                    packet = create_packet(pid, sequence)
                except Exception:
                    print("Failed to create ICMP packet")
                    continue
                send_time = time.time()
                try:
                    sock.sendto(packet, (dest_addr, 1))
                    packets_sent += 1
                except PermissionError:
                    print("Permission denied: ICMP messages require admin privileges")
                    sys.exit()
                except socket.error as e:
                    print(f"Socket error: {e}")
                    continue

                try:
                    ready = select.select([sock], [], [], timeout)
                    if ready[0] == []:
                        print(f"Request timed out for seq={sequence}")
                        continue
                    recv_packet, addr = sock.recvfrom(1024)
                    recv_time = time.time()
                    icmp_type, code, resp_id, resp_seq = parse_icmp_packet(recv_packet)
                    if icmp_type is None:
                        print(f"Received malformed packet for seq={sequence}")
                        continue
                    if icmp_type == ICMP_ECHO_REPLY:
                        if resp_id != pid:
                            print(f"Ignoring ICMP Echo Reply: mismatched id (expected {pid}, got {resp_id}) for seq={sequence}")
                            continue
                        elif resp_seq != sequence:
                            print(f"Ignoring ICMP Echo Reply: mismatched sequence (expected {sequence}, got {resp_seq})")
                            continue
                        else:
                            rtt = (recv_time - send_time) * 1000
                            rtts.append(rtt)
                            packets_received += 1
                            min_rtt = min(rtts)
                            avg_rtt = statistics.mean(rtts)
                            max_rtt = max(rtts)
                            if len(rtts) > 1:
                                stdev = statistics.stdev(rtts)
                                print(f"Reply from {addr[0]}: seq={sequence} time={rtt:.2f} ms (min/avg/max/mdev = {min_rtt:.2f}/{avg_rtt:.2f}/{max_rtt:.2f}/{stdev:.2f} ms)")
                            else:
                                print(f"Reply from {addr[0]}: seq={sequence} time={rtt:.2f} ms (min/avg/max = {min_rtt:.2f}/{avg_rtt:.2f}/{max_rtt:.2f} ms)")
                    elif icmp_type == ICMP_DEST_UNREACH:
                        msg = ICMP_UNREACH_CODES.get(code, f"Unknown code {code}")
                        print(f"Destination unreachable ({msg}) for seq={sequence}")
                    elif icmp_type == ICMP_TIME_EXCEEDED:
                        print(f"Time to live exceeded for seq={sequence}")
                    else:
                        print(f"Unexpected ICMP type={icmp_type} code={code} for seq={sequence}")
                except socket.timeout:
                    print(f"Request timed out for seq={sequence}")
                except socket.error as e:
                    if hasattr(e, 'errno'):
                        if e.errno == errno.ENETUNREACH:
                            print(f"Network unreachable for seq={sequence}")
                        elif e.errno == errno.EHOSTUNREACH:
                            print(f"Host unreachable for seq={sequence}")
                        else:
                            print(f"Socket error [{e.errno}] for seq={sequence}: {e}")
                    else:
                        print(f"Socket error for seq={sequence}: {e}")
                except Exception as e:
                    print(f"Error for seq={sequence}: {e}")
                time.sleep(1)

    except PermissionError:
        print("Permission denied: ICMP messages require admin privileges")
        sys.exit()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

    print_stats(host, packets_sent, packets_received, rtts)

if __name__ == '__main__':
    ping(sys.argv[1], count=int(sys.argv[2]) if len(sys.argv) > 2 else 4)
