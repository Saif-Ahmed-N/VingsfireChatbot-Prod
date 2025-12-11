import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    # Default to 587 if not set
    smtp_port = int(os.getenv("EMAIL_PORT", 587)) 

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
            print(f"Error attaching file: {e}")

    try:
        # --- THE FIX: Use standard SMTP with STARTTLS (Port 587) ---
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Helps see what's happening in logs
        server.starttls()         # Upgrade connection to secure
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False