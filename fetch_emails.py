import os
import imaplib
import email
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

# Configuration
CLIENT_SECRET_FILE = "credentials.json"
CREDENTIALS_FILE = "token.json"

def load_credentials():
    """"Loads credentials from the CREDENTIALS_FILE if it exists, else creates a new one."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'rb') as token:
            creds = pickle.load(token)
        # Refresh credentials if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        creds = flow.run_local_server(port=0)
        with open(CREDENTIALS_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def fetch_emails(creds):
    """"Fetches emails using the provided credentials."""
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    try:
        mail.login(creds.token, 'xoauth2')
    except imaplib.IMAP4.error as e:
        print(f"Authentication failed: {e}")
        return []
    mail.select("inbox")

    # Search for emails with the keyword in the subject
    result, email_ids = mail.search(None, '(SUBJECT "Python")')
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

if __name__ == "__main__":
    creds = load_credentials()
    emails = fetch_emails(creds)
    if emails:
        print("\n".join(emails))
    else:
        print("No new emails found.")