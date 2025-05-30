import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import subprocess
import platform
import threading
import uuid
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import re
import time

class NetworkScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сетевой сканер")

        self.lock = threading.Lock()
        self.scanned_ips = 0
        self.finished = False
        self.results = []

        input_frame = ttk.Frame(root)
        input_frame.pack(pady=5)
        ttk.Label(input_frame, text="Маска (например, 192.168.3.0):").pack(side='left')
        self.network_entry = ttk.Entry(input_frame)
        self.network_entry.insert(0, "192.168.3.0")
        self.network_entry.pack(side='left', padx=5)

        self.mode = tk.StringVar(value="default")
        mode_frame = ttk.LabelFrame(root, text="Режим сканирования")
        mode_frame.pack(pady=5, fill='x')
        ttk.Radiobutton(mode_frame, text="По умолчанию", variable=self.mode, value="default").pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text="(/22)", variable=self.mode, value="fast").pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text="(/16)", variable=self.mode, value="thorough").pack(side='left', padx=10)

        self.scan_button = ttk.Button(root, text="Начать сканирование", command=self.start_scan)
        self.scan_button.pack(pady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(root, width=90, height=30)
        self.result_text.pack(pady=10)

        self.status_label = ttk.Label(root, text="Готово к сканированию")
        self.status_label.pack(pady=5)

    def get_selected_subnet(self):
        base_ip = self.network_entry.get().strip()
        if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", base_ip):
            return None
        if self.mode.get() == "fast":
            return f"{base_ip}/22"
        elif self.mode.get() == "thorough":
            return f"{base_ip}/16"
        else:
            return f"{base_ip}/24"

    def generate_ips(self, subnet):
        net = ipaddress.ip_network(subnet, strict=False)
        return [str(ip) for ip in net.hosts()]

    def start_scan(self):
        self.scan_button.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        self.results.clear()
        self.scanned_ips = 0
        self.finished = False

        subnet = self.get_selected_subnet()
        if not subnet:
            self.status_label.config(text="Ошибка: введите корректный IP")
            self.scan_button.config(state=tk.NORMAL)
            return

        self.status_label.config(text=f"Сканирование подсети {subnet}...")

        try:
            self.all_ips = self.generate_ips(subnet)
        except ValueError:
            self.status_label.config(text="Ошибка: недопустимая подсеть")
            self.scan_button.config(state=tk.NORMAL)
            return

        self.total_ips = len(self.all_ips)
        self.progress.config(maximum=self.total_ips)

        threading.Thread(target=self.scan_network_thread, daemon=True).start()
        self.update_progress_loop()

    def scan_network_thread(self):
        with ThreadPoolExecutor(max_workers=100) as executor:
            for ip in self.all_ips:
                executor.submit(self.scan_ip, ip)
        threading.Thread(target=self.fetch_from_arp_after_ping, daemon=True).start()

    def scan_ip(self, ip):
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", "300", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]

        mac = "неизвестен"
        hostname = "неизвестно"
        source = "none"

        ping_ok = False

        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                ping_ok = True
                # print(f"{ip} ОТВЕТИЛ на ping")
                time.sleep(0.3)
            else:
                time.sleep(0)
                # print(f"{ip} не отвечает на ping")
        except Exception as e:
            print(f"[ERR] Ошибка при пинге {ip}: {e}")

        mac = self.get_mac_from_arp(ip)
        if mac != "неизвестен":
            source = "arp" if not ping_ok else "ping+arp"
        elif ping_ok:
            source = "ping"

        if ping_ok or mac != "неизвестен":
            hostname = self.get_hostname(ip)
            with self.lock:
                if not any(r[0] == ip for r in self.results):
                    self.results.append((ip, mac, hostname, source))

        with self.lock:
            self.scanned_ips += 1

    def fetch_from_arp_after_ping(self):
        threading.Event().wait(3)
        try:
            arp_output = subprocess.check_output("arp -a", shell=True).decode(errors='ignore')
            for line in arp_output.splitlines():
                match_ip = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                match_mac = re.search(r"((?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})", line)
                if match_ip and match_mac:
                    ip = match_ip.group(1)
                    mac = match_mac.group(1).replace('-', ':').lower()
                    if mac == "ff:ff:ff:ff:ff:ff":
                        continue
                    hostname = self.get_hostname(ip)
                    with self.lock:
                        if not any(r[0] == ip for r in self.results):
                            self.results.append((ip, mac, hostname))
        except Exception as e:
            print("ARP error:", e)
        self.finished = True

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "неизвестно"
    
    def get_mac_from_arp(self, ip):
        try:
            system = platform.system().lower()
            if system == "windows":
                output = subprocess.check_output(["arp", "-a"], encoding='utf-8')
            elif system == "darwin":
                output = subprocess.check_output(["arp", ip], encoding='utf-8')
            else:
                output = subprocess.check_output(["arp", "-n"], encoding='utf-8')

            for line in output.splitlines():
                if ip in line:
                    mac_match = re.search(r"((?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})", line)
                    if mac_match:
                        return mac_match.group(1).replace('-', ':').lower()
        except Exception as e:
            print(f"[ERR] ARP error for {ip}: {e}")
        return None

    def get_local_info(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = "неизвестно"
        mac = ':'.join(f"{b:02x}" for b in uuid.getnode().to_bytes(6, 'big'))
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = socket.gethostname()
        return {"ip": ip, "mac": mac, "name": hostname}

    def update_progress_loop(self):
        self.progress['value'] = self.scanned_ips
        if self.finished and self.scanned_ips >= self.total_ips:
            self.show_results()
        else:
            self.root.after(300, self.update_progress_loop)

    def show_results(self):
        self.status_label.config(text="Сканирование завершено")
        self.scan_button.config(state=tk.NORMAL)

        local = self.get_local_info()

        self.result_text.insert(tk.END, "Ваш компьютер:\n")
        self.result_text.insert(tk.END, f"{'IP-адрес':<16}{'MAC-адрес':<20}{'Имя устройства':<25}{'Источник'}\n")
        self.result_text.insert(tk.END, f"{local['ip']:<16}{local['mac']:<20}{local['name']:<25}локальный\n\n")

        self.result_text.insert(tk.END, "Найденные устройства в сети:\n")
        self.result_text.insert(tk.END, f"{'IP-адрес':<16}{'MAC-адрес':<20}{'Имя устройства':<25}{'Источник'}\n")

        for ip, mac, hostname, source in sorted(self.results):
            if ip == local['ip']:
                continue

            ip = str(ip) if ip else "неизвестно"
            mac = str(mac) if mac else "неизвестен"
            hostname = str(hostname) if hostname else "неизвестно"
            source = str(source) if source else "unknown"

            if mac != "неизвестен" or source == "ping+arp":
                self.result_text.insert(tk.END, f"{ip:<16}{mac:<20}{hostname:<25}{source}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkScannerApp(root)
    root.mainloop()
