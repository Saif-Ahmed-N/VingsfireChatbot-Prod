import os
import resend
import base64

def send_email_with_attachment(receiver_email, subject, body, attachment_path=None):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("❌ Error: RESEND_API_KEY is missing.")
        return False

    resend.api_key = api_key

    # For testing, you MUST use this email until you verify your own domain
    sender_email = "onboarding@resend.dev" 
    
    # Prepare attachment params
    attachments = []
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                file_data = list(f.read()) # Resend expects a list of integers (bytes)
            
            attachments.append({
                "filename": os.path.basename(attachment_path),
                "content": file_data
            })
        except Exception as e:
            print(f"⚠️ Error preparing attachment: {e}")

    try:
        print(f"📧 Sending email via Resend API to {receiver_email}...")
        
        params = {
            "from": f"Infinite Tech AI <{sender_email}>",
            "to": [receiver_email],
            "subject": subject,
            "html": f"<p>{body.replace(chr(10), '<br>')}</p>",
            "attachments": attachments
        }

        r = resend.Emails.send(params)
        print(f"✅ Email sent successfully! ID: {r.get('id')}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email via Resend: {e}")
        return False