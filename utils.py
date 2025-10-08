import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_email_with_attachment(receiver_email, subject, body, attachment_path):
    smtp_server = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT"))
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        raise ValueError("Email credentials are not fully configured in the .env file.")

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)

    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)