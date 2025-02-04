from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import requests

def load_credentials():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_emails(creds):
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    try:
        mail.login(creds.token, 'xoauth2')
    except imaplib.IMAP4.error as e:
        print(f"Authentication failed: {e}")
        return []
    mail.select("inbox")
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
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
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