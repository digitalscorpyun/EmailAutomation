import imaplib
import email
import os
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --------------------------------
# CONFIGURATION
# --------------------------------
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

GMAIL_USER = "mikerkibbe73@gmail.com"
TO_EMAIL = "mikerkibbe73@gmail.com"

OBSIDIAN_PATH = r"C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"

EMAIL_LIMIT = 10  # Number of emails to fetch

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# --------------------------------
# AUTHENTICATION FUNCTION
# --------------------------------
def authenticate_gmail():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

# --------------------------------
# FETCH EMAILS FUNCTION
# --------------------------------
def fetch_emails():
    creds = authenticate_gmail()
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(GMAIL_USER, creds.token)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()[-EMAIL_LIMIT:]  # Get latest emails

    categories = {
        "Important": [],
        "Job Alerts": [],
        "From Keywords": [],
        "Other": []
    }

    keywords = ["AI", "Machine Learning", "Data Science", "Stargate"]  # Keywords to filter

    for num in email_ids:
        result, msg_data = mail.fetch(num, "(RFC822)")
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
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                email_entry = f"### 📧 {subject}\n- **From:** {sender}\n- **Date:** {date}\n\n{body[:300]}...\n---\n"

                # Categorization logic
                if "alert" in subject.lower() or "security" in subject.lower():
                    categories["Important"].append(email_entry)
                elif "job" in subject.lower() or "hiring" in subject.lower():
                    categories["Job Alerts"].append(email_entry)
                elif any(keyword.lower() in subject.lower() for keyword in keywords):
                    categories["From Keywords"].append(email_entry)
                else:
                    categories["Other"].append(email_entry)

    mail.logout()
    return categories

# --------------------------------
# SAVE TO OBSIDIAN FUNCTION
# --------------------------------
def save_to_obsidian(categories):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    note_content = f"# 📨 Email Sync Log ({timestamp})\n\n"

    for category, emails in categories.items():
        if emails:
            note_content += f"## {category}\n" + "\n".join(emails) + "\n"

    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write(note_content)

    print(f"✅ Emails saved to Obsidian at {OBSIDIAN_PATH}")

# --------------------------------
# SEND NOTIFICATION FUNCTION
# --------------------------------
def send_email_notification(success=True):
    subject = "✅ Email Sync Successful" if success else "⚠️ Email Sync Failed"
    body = f"Email sync to Obsidian completed successfully!\nFile saved at: {OBSIDIAN_PATH}" if success else "Email sync encountered an issue."

    msg = MIMEText(body)
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, "your-app-password")  # Use App Password if needed
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")

# --------------------------------
# MAIN EXECUTION
# --------------------------------
if __name__ == "__main__":
    categories = fetch_emails()
    success = save_to_obsidian(categories)
    send_email_notification(success)
    print("✅ Email fetching complete!")
