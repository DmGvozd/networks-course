import socket
import base64
import mimetypes
import os
import uuid
import ssl
from getpass import getpass

def send_email_with_attachment(recipient_email, message_text, attachment_path):
    sender_email = input("Введите Gmail отправителя: ")
    sender_password = getpass("Введите пароль от почты отправителя: ")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    boundary = f"----=_NextPart_{uuid.uuid4()}"

    headers = f"From: {sender_email}\r\n"
    headers += f"To: {recipient_email}\r\n"
    headers += f"Subject: Email with image from Dmitry Gvozd\r\n"
    headers += f"MIME-Version: 1.0\r\n"
    headers += f"Content-Type: multipart/mixed; boundary=\"{boundary}\"\r\n\r\n"

    mime_message = f"--{boundary}\r\n"
    mime_message += "Content-Type: text/plain; charset=\"utf-8\"\r\n"
    mime_message += "Content-Transfer-Encoding: 7bit\r\n\r\n"
    mime_message += f"{message_text}\r\n\r\n"

    try:
        with open(attachment_path, "rb") as f:
            attachment_data = f.read()
        
        encoded_attachment = base64.b64encode(attachment_data).decode('ascii')
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        filename = os.path.basename(attachment_path)

        mime_message += f"--{boundary}\r\n"
        mime_message += f"Content-Type: {mime_type}; name=\"{filename}\"\r\n"
        mime_message += f"Content-Disposition: attachment; filename=\"{filename}\"\r\n"
        mime_message += "Content-Transfer-Encoding: base64\r\n\r\n"
        
        chunk_size = 76 
        for i in range(0, len(encoded_attachment), chunk_size):
            mime_message += encoded_attachment[i:i+chunk_size] + "\r\n"
        mime_message += "\r\n"

    except FileNotFoundError:
        print(f"Ошибка: Файл вложения не найден по пути: {attachment_path}")
        return
    except Exception as e:
        print(f"Ошибка при обработке вложения: {e}")
        return
        
    mime_message += f"--{boundary}--\r\n"
    
    full_message = headers + mime_message
    full_message += ".\r\n"
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((smtp_server, smtp_port))
        response = client_socket.recv(1024).decode()
        if not response.startswith('220'):
            raise Exception(f'220 reply not received from server. Got: {response}')

        client_socket.send(b'EHLO [127.0.0.1]\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception(f'250 reply not received from server after EHLO. Got: {response}')

        client_socket.send(b'STARTTLS\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('220'):
            raise Exception(f'220 reply not received from server on STARTTLS. Got: {response}')

        context = ssl.create_default_context()
        client_socket = context.wrap_socket(client_socket, server_hostname=smtp_server)

        client_socket.send(b'EHLO [127.0.0.1]\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception(f'250 reply not received from server after STARTTLS EHLO. Got: {response}')

        client_socket.send(b'AUTH LOGIN\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('334'):
            raise Exception(f'334 reply not received from server for AUTH LOGIN. Got: {response}')

        client_socket.send(base64.b64encode(sender_email.encode()) + b'\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('334'):
            raise Exception(f'334 reply not received for username. Got: {response}')

        client_socket.send(base64.b64encode(sender_password.encode()) + b'\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('235'):
            try:
                response += client_socket.recv(1024).decode()
            except socket.timeout:
                 pass
            raise Exception(f'Authentication failed. Server reply: {response}')

        client_socket.send(f'MAIL FROM:<{sender_email}>\r\n'.encode())
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception(f'250 reply not received from server for MAIL FROM. Got: {response}')

        client_socket.send(f'RCPT TO:<{recipient_email}>\r\n'.encode())
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            raise Exception(f'250 reply not received from server for RCPT TO. Got: {response}')

        client_socket.send(b'DATA\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('354'):
            raise Exception(f'354 reply not received from server for DATA. Got: {response}')

        client_socket.send(full_message.encode('utf-8'))
        
        response = client_socket.recv(1024).decode()
        if not response.startswith('250'):
            try:
                 response += client_socket.recv(1024).decode()
            except socket.timeout:
                 pass
            raise Exception(f'250 reply not received after sending message body. Got: {response}')

        client_socket.send(b'QUIT\r\n')
        response = client_socket.recv(1024).decode()
        if not response.startswith('221'): 
             print(f"Warning: Expected 221 on QUIT, but got: {response}")

        client_socket.close()
        print(f"Сообщение с вложением успешно отправлено на {recipient_email}")

    except socket.gaierror as e:
        print(f"Ошибка разрешения имени сервера ({smtp_server}): {e}")
    except socket.timeout:
        print("Ошибка: Истекло время ожидания ответа от сервера.")
    except ssl.SSLError as e:
        print(f"Ошибка SSL/TLS: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if 'client_socket' in locals() and client_socket.fileno() != -1:
            try:
                client_socket.close()
            except Exception:
                pass

if __name__ == "__main__":
    recipient = input("Введите email получателя: ")
    message = input("Введите текст сообщения: ")
    attachment = input("Введите полный путь к файлу изображения для вложения: ")
    
    if not os.path.exists(attachment):
        print(f"Ошибка: Файл не найден по указанному пути: {attachment}")
    elif not os.path.isfile(attachment):
         print(f"Ошибка: Указанный путь не является файлом: {attachment}")
    else:
        send_email_with_attachment(recipient, message, attachment)
