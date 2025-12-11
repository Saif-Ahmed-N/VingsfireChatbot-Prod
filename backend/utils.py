import os
import requests
import base64

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    # Load keys
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_SECRET_KEY")
    sender_email = os.getenv("EMAIL_ADDRESS") # Your verified Mailjet email

    if not api_key or not api_secret:
        print("❌ Error: Mailjet Keys are missing.")
        return False

    url = "https://api.mailjet.com/v3.1/send"
    auth = (api_key, api_secret)

    # Base64 encode the attachment
    attachments = []
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                encoded_file = base64.b64encode(f.read()).decode('utf-8')
            
            attachments.append({
                "ContentType": "application/pdf",
                "Filename": os.path.basename(attachment_path),
                "Base64Content": encoded_file
            })
        except Exception as e:
            print(f"⚠️ Error preparing attachment: {e}")

    # Mailjet JSON Payload
    data = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "Infinite Tech AI"
                },
                "To": [
                    {
                        "Email": receiver_email
                    }
                ],
                "Subject": subject,
                "HTMLPart": f"<p>{body.replace(chr(10), '<br>')}</p>",
                "Attachments": attachments
            }
        ]
    }

    try:
        print(f"📧 Sending email via Mailjet API to {receiver_email}...")
        response = requests.post(url, auth=auth, json=data)
        
        if response.status_code == 200:
            print(f"✅ Email sent successfully! Response: {response.json()['Messages'][0]['Status']}")
            return True
        else:
            print(f"❌ Failed to send email. Status: {response.status_code}")
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return False