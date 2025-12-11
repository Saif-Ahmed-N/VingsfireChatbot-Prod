import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import socket

# --- CRITICAL FIX: Force IPv4 to prevent Hanging/Network Unreachable ---
# Render/Docker sometimes hangs on IPv6. This forces it to use IPv4.
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo
# -----------------------------------------------------------------------

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD") # Your 16-char App Password
    smtp_server = "smtp.gmail.com"
    smtp_port = 465 # SSL Port (Most reliable on Cloud)

    print(f"📧 DEBUG: Attempting connection to {smtp_server}:{smtp_port} (IPv4 Enforced)...")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF if it exists
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
        # Use SMTP_SSL directly (Skip the STARTTLS handshake that often hangs)
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20) 
        
        server.set_debuglevel(1) # Show interaction in logs
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        print(f"✅ Email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False