# backend/utils.py

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load the .env file variables
load_dotenv()

# Get Configuration from .env
SMTP_SERVER = os.getenv("EMAIL_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 465))
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ Error: Email credentials missing in .env")
        return

    try:
        # 1. Setup the Message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # 2. Attach File (PDF) if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        # 3. Connect to Gmail Server
        # Note: Port 465 uses SSL
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # 4. Send Email
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully to {receiver_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")