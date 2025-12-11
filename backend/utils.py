import os
import requests
import base64

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_name = "Infinite Tech AI" # You can customize this

    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    # Prepare the email data
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": receiver_email}],
        "subject": subject,
        "htmlContent": f"<p>{body.replace(chr(10), '<br>')}</p>" # Convert newlines to HTML breaks
    }

    # Handle Attachment
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode()
            
            payload["attachment"] = [
                {
                    "content": encoded_string,
                    "name": os.path.basename(attachment_path)
                }
            ]
        except Exception as e:
            print(f"⚠️ Error preparing attachment: {e}")

    try:
        print(f"📧 Sending email via Brevo API to {receiver_email}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Email sent successfully! Message ID: {response.json().get('messageId')}")
            return True
        else:
            print(f"❌ Failed to send email. Status: {response.status_code}")
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return False