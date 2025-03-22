import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass

def send_email(recipient_email, message_format):
    try:
        sender_email = input("Введите Gmail отправителя: ")
        sender_password = getpass("Введите пароль от почты отправителя: ")

        if message_format.lower() not in ("txt", "html"):
            raise ValueError("Неподдерживаемый формат сообщения. Доступны: txt, html")

        message = MIMEMultipart("alternative")
        message["Subject"] = "Email from Dmitry Gvozd"
        message["From"] = sender_email
        message["To"] = recipient_email

        if message_format.lower() == "txt":
            text = "Dmitry Gvozd в формате txt."
            part = MIMEText(text, "plain")
        elif message_format.lower() == "html":
            html = """\
            <html>
              <head></head>
              <body>
                <p><b>Dmitry Gvozd</b> в формате HTML.</p>
              </body>
            </html>
            """
            part = MIMEText(html, "html")

        message.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print(f"Сообщение успешно отправлено на {recipient_email}")

    except ValueError as ve:
        print(f"Ошибка: {ve}")
    except smtplib.SMTPAuthenticationError:
        print("Ошибка аутентификации. Проверьте email и пароль.")
    except smtplib.SMTPRecipientsRefused:
        print("Ошибка: Неверный адрес получателя.")
    except smtplib.SMTPServerDisconnected:
        print("Ошибка: Сервер неожиданно отключился.")
    except smtplib.SMTPException as e:
        print(f"Ошибка SMTP: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
    

if __name__ == "__main__":
    recipient = input("Введите email получателя: ")
    format_choice = input("Введите формат сообщения (txt или html): ")
    send_email(recipient, format_choice)
