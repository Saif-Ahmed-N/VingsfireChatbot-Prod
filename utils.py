import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
import base64
from dotenv import load_dotenv

load_dotenv()

def send_email_with_attachment(receiver_email, subject, body, attachment_path):
    sender_email = os.getenv("EMAIL_ADDRESS")
    api_key = os.getenv("SENDGRID_API_KEY")

    if not all([sender_email, api_key]):
        raise ValueError("SendGrid credentials (EMAIL_ADDRESS, SENDGRID_API_KEY) are not fully configured.")

    message = Mail(
        from_email=sender_email,
        to_emails=receiver_email,
        subject=subject,
        html_content=body.replace('\n', '<br>'))

    with open(attachment_path, 'rb') as f:
        data = f.read()
    encoded_file = base64.b64encode(data).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName(os.path.basename(attachment_path)),
        FileType('application/pdf'),
        Disposition('attachment')
    )
    message.attachment = attachedFile

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # --- CRITICAL BUG FIX: ADDED DETAILED LOGGING ---
        if response.status_code >= 300: # Check if the status code is an error (3xx, 4xx, 5xx)
            print(f"SendGrid ERROR for email to {receiver_email}:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Body: {response.body}")
            print(f"  Response Headers: {response.headers}")
        else:
            print(f"SendGrid SUCCESS for email to {receiver_email}: Status Code {response.status_code}")

    except Exception as e:
        # This will catch network errors or problems with the library itself
        print(f"CRITICAL ERROR sending email with SendGrid to {receiver_email}: {e}")