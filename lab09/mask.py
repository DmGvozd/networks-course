import socket
import struct
import platform
import subprocess
import re

def get_ip_and_mask():
    system = platform.system()
    if system == "Windows":
        output = subprocess.check_output("ipconfig", encoding="utf-8")
        adapters = output.split("\n\n")
        for adapter in adapters:
            if "IPv4 Address" in adapter or "IPv4-адрес" in adapter:
                ip_match = re.search(r"IPv4[^\d]*(\d+\.\d+\.\d+\.\d+)", adapter)
                mask_match = re.search(r"Subnet Mask[^\d]*(\d+\.\d+\.\d+\.\d+)", adapter)
                if ip_match and mask_match:
                    return ip_match.group(1), mask_match.group(1)
    else:
        output = subprocess.check_output("ifconfig", encoding="utf-8")
        interfaces = re.split(r'\n(?=\S)', output)
        for interface in interfaces:
            ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", interface)
            mask_match = re.search(r"netmask (0x[0-9a-f]+|\d+\.\d+\.\d+\.\d+)", interface)
            if ip_match and mask_match:
                ip = ip_match.group(1)
                mask = mask_match.group(1)
                if mask.startswith("0x"):
                    mask = socket.inet_ntoa(struct.pack(">I", int(mask, 16)))
                if ip != "127.0.0.1":
                    return ip, mask
    return None, None

ip, mask = get_ip_and_mask()

if ip and mask:
    print(f"IP-адрес: {ip}")
    print(f"Маска сети: {mask}")
else:
    print("Не удалось определить IP-адрес и маску сети")
