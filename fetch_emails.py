import os
import json
import base64
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# -----------------------------
# CONFIGURATION
# -----------------------------

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
OBSIDIAN_PATH = r"C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"
EMAIL_LIMIT = 10  # Adjust as needed

# Categorization Keywords
IMPORTANT_KEYWORDS = ["security alert", "account notice", "urgent"]
JOB_ALERT_KEYWORDS = ["job alert", "hiring", "career opportunity"]
TOPIC_KEYWORDS = ["AI", "ML", "Data Science", "Stargate"]  # Customize as needed

# -----------------------------
# AUTHENTICATION
# -----------------------------

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

# -----------------------------
# FETCH EMAILS FROM GMAIL
# -----------------------------

def fetch_emails():
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", maxResults=EMAIL_LIMIT).execute()
    messages = results.get("messages", [])

    categorized_emails = {
        "Important": [],
        "Job Alerts": [],
        "From Keywords": [],
        "Other": [],
    }

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "(No Date)")

        body = "(No Content)"
        if "parts" in msg_data["payload"]:
            for part in msg_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
                    break

        # Categorize emails
        email_entry = f"#### 📧 {subject}\n- **From:** {sender}\n- **Date:** {date}\n\n{body.strip()}\n---\n"

        if any(word.lower() in subject.lower() for word in IMPORTANT_KEYWORDS):
            categorized_emails["Important"].append(email_entry)
        elif any(word.lower() in subject.lower() for word in JOB_ALERT_KEYWORDS):
            categorized_emails["Job Alerts"].append(email_entry)
        elif any(word.lower() in subject.lower() for word in TOPIC_KEYWORDS):
            categorized_emails["From Keywords"].append(email_entry)
        else:
            categorized_emails["Other"].append(email_entry)

    return categorized_emails

# -----------------------------
# SAVE TO OBSIDIAN
# -----------------------------

def save_to_obsidian(categorized_emails):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    email_log = f"# 📥 Email Sync Log ({timestamp})\n\n"

    for category, emails in categorized_emails.items():
        if emails:
            email_log += f"## {category}\n" + "\n".join(emails) + "\n"

    os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)

    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write(email_log)

    print(f"✅ Emails categorized and saved to Obsidian at {OBSIDIAN_PATH}")

# -----------------------------
# MAIN EXECUTION
# -----------------------------

if __name__ == "__main__":
    categories = fetch_emails()
    save_to_obsidian(categories)
    print("✅ Email fetching and sorting complete!")
