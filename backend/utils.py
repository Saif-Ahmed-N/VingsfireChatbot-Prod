import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import socket

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    # Load variables
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    # FIX: Try using googlemail.com alias if gmail.com fails
    smtp_server = os.getenv("EMAIL_HOST", "smtp.googlemail.com") 
    
    # Ensure port is an integer
    try:
        smtp_port = int(os.getenv("EMAIL_PORT", 587))
    except ValueError:
        smtp_port = 587

    print(f"📧 DEBUG: Connecting to {smtp_server}:{smtp_port} for {receiver_email}...")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)
        except Exception as e:
            print(f"⚠️ Error attaching file: {e}")

    try:
        # Establish Connection
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30) # Added timeout
        server.set_debuglevel(1) 
        server.starttls() 
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False