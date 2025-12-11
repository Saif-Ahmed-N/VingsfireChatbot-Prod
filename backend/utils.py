import yagmail
import os

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD") # Your 16-char App Password

    try:
        # Initialize Yagmail (Handles Ports/SSL automatically)
        yag = yagmail.SMTP(sender_email, sender_password)

        contents = [
            body,
            attachment_path # Yagmail handles file attachment logic automatically
        ]

        print(f"📧 Sending email via Yagmail to {receiver_email}...")
        
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=contents
        )
        
        print(f"✅ Email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False