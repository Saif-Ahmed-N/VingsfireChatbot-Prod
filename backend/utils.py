import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import socket

# --- THE FIX: Force IPv4 to prevent Network Unreachable / Hanging errors ---
# This tells Python: "If you see an IPv6 address for Gmail, ignore it. Only use IPv4."
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo
# --------------------------------------------------------------------------

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    
    try:
        # Default to 587 (TLS) as it's most reliable with IPv4
        smtp_port = int(os.getenv("EMAIL_PORT", 587))
    except ValueError:
        smtp_port = 587

    print(f"📧 DEBUG: Connecting to {smtp_server}:{smtp_port} (IPv4 Forced)...")

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
        # Connect using Standard SMTP (IPv4 enforced)
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.set_debuglevel(1) 
        
        # Start TLS (Secure Handshake)
        server.starttls()
        
        # Login and Send
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        print(f"✅ Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False