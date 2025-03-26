import socket
import re

class FTPClient:
    def __init__(self, host, user, password):
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_sock.connect((host, 21))
        self.read_response()
        self.send_command(f"USER {user}")
        self.send_command(f"PASS {password}")
    
    def send_command(self, cmd):
        self.control_sock.send(f"{cmd}\r\n".encode())
        return self.read_response()
    
    def read_response(self):
        response = ""
        while True:
            part = self.control_sock.recv(1024).decode()
            response += part
            if part.endswith("\r\n"): break
        return response
    
    def passive_mode(self):
        resp = self.send_command("PASV")
        matches = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', resp)
        ip = '.'.join(matches.groups()[:4])
        port = int(matches.group(5)) * 256 + int(matches.group(6))
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((ip, port))
        return data_sock
    
    def list_files(self):
        data_sock = self.passive_mode()
        self.send_command("LIST")
        data = b""
        while True:
            chunk = data_sock.recv(4096)
            if not chunk: break
            data += chunk
        data_sock.close()
        print(self.read_response())
        print(data.decode())
    
    def upload(self, local_path, remote_path):
        data_sock = self.passive_mode()
        self.send_command(f"STOR {remote_path}")
        with open(local_path, 'rb') as f:
            data_sock.sendall(f.read())
        data_sock.close()
        print(self.read_response())
    
    def download(self, remote_path, local_path):
        data_sock = self.passive_mode()
        self.send_command(f"RETR {remote_path}")
        with open(local_path, 'wb') as f:
            while True:
                chunk = data_sock.recv(4096)
                if not chunk: break
                f.write(chunk)
        data_sock.close()
        print(self.read_response())

if __name__ == "__main__":
    ftp = FTPClient("ftp.dlptest.com", "dlpuser", "rNrKYTX9g7z3RgJRmxWuGHbeu")
    
    while True:
        cmd = input("ftp> ").split()
        if not cmd: continue
        
        if cmd[0] == "list":
            ftp.list_files()
        
        elif cmd[0] == "upload" and len(cmd) == 3:
            ftp.upload(cmd[1], cmd[2])
        
        elif cmd[0] == "download" and len(cmd) == 3:
            ftp.download(cmd[1], cmd[2])
        
        elif cmd[0] == "exit":
            ftp.send_command("QUIT")
            break
        
        else:
            print("""Доступные команды:\n - list\n - upload <local_file> <remote_file>\n - download <remote_file> <local_file>\n - exit\n""")
