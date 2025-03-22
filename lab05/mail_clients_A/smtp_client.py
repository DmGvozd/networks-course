import socket
import base64
import ssl
from getpass import getpass

def send_email_via_sockets(recipient_email, message_text):
    sender_email = input("Введите Gmail отправителя: ")
    sender_password = getpass("Введите пароль от почты отправителя: ")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((smtp_server, smtp_port))
        response = client_socket.recv(1024).decode()
        if not response.startswith('220'):
            raise Exception('220 reply not received from server.')

        client_socket.send(b'EHLO [127.0.0.1]\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception('250 reply not received from server.')
        
        client_socket.send(b'STARTTLS\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('220'):
            raise Exception('220 reply not received from server on STARTTLS')
        
        context = ssl.create_default_context()
        client_socket = context.wrap_socket(client_socket, server_hostname=smtp_server)

        client_socket.send(b'EHLO [127.0.0.1]\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception('250 reply not received from server after STARTTLS.')

        client_socket.send(b'AUTH LOGIN\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('334'):
            raise Exception('334 reply not received from server.')

        client_socket.send(base64.b64encode(sender_email.encode()) + b'\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('334'):
            raise Exception('334 reply not received from server.')

        client_socket.send(base64.b64encode(sender_password.encode()) + b'\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('235'):
            raise Exception('235 reply not received from server.')
        
        client_socket.send(f'MAIL FROM:<{sender_email}>\r\n'.encode())
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception('250 reply not received from server.')

        client_socket.send(f'RCPT TO:<{recipient_email}>\r\n'.encode())
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception('250 reply not received from server.')

        client_socket.send(b'DATA\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('354'):
            raise Exception('354 reply not received from server.')

        message = f'Subject: Email from Dmitry Gvozd\r\nFrom: {sender_email}\r\nTo: {recipient_email}\r\n\r\n{message_text}\r\n.\r\n'
        client_socket.send(message.encode())
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception('250 reply not received from server.')

        client_socket.send(b'QUIT\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('221'):
            raise Exception('221 reply not received from server.')

        client_socket.close()
        print(f"Сообщение успешно отправлено на {recipient_email}")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    recipient = input("Введите email получателя: ")
    message = input("Введите текст сообщения: ")
    send_email_via_sockets(recipient, message)
