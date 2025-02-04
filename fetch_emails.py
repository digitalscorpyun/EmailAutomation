import os
import imaplib
import email
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"
EMAIL_LIMIT = 10
KEYWORD = 'Python'

# Load credentials from environment variables
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')

def load_credentials():
    """"Loads credentials from the CREDENTIALS_FILE if it exists, else creates a new one."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'rb') as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        creds = flow.run_local_server(port=0)
        with open(CREDENTIALS_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def fetch_emails(creds):
    """Fetches emails using the provided credentials."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(creds.token, 'xoauth2')
    mail.select("inbox")

    # Search for emails with the keyword in the subject
    result, email_ids = mail.search(None, f'(SUBJECT "{KEYWORD}")')
    email_ids = result[0].split()

    email_entries = []
    for num in email_ids[-EMAIL_LIMIT:]:
        result, msg_data = mail.fetch(num, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                raw_email = response_part[1]
                msg = email.message_from_bytes(raw_email)

                subject = msg["Subject"] or "(No Subject)"
                sender = msg["From"] or "(Unknown Sender)"
                date = msg["Date"] or "(No Date)"
                body = ""

                # Extract email body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # Format email entry
                email_entry = f"### 📧 {subject}\n- **From:** {sender}\n- **Date:** {date}\n\n{body}\n---\n"
                email_entries.append(email_entry)

    mail.logout()
    return email_entries

def save_to_obsidian(emails):
    """Saves the fetched emails to an Obsidian file."""
    if not emails:
        print("⚠️ No new emails found.")
        return False

    os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)

    with open(OBSIDIAN_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## 🗓️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n".join(emails))

    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")
    return True

def send_email_notification(success=True):
    """Sends an email notification about the sync status."""
    subject = "✅ Email Sync Successful" if success else "⚠️ Email Sync Failed"
    body = f"Email sync to Obsidian completed successfully!\nFile saved at: {OBSIDIAN_PATH}" if success else "Email sync encountered an issue."

    msg = MIMEText(body)
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")

if __name__ == "__main__":
    creds = load_credentials()
    emails = fetch_emails(creds)
    success = save_to_obsidian(emails)
    send_email_notification(success)
    print("✅ Email fetching complete!")