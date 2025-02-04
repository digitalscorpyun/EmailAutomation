import os
import json
import base64
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --------------------------------
# CONFIGURATION
# --------------------------------
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

GMAIL_USER = "mikerkibbe73@gmail.com"
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
# FETCH EMAILS USING GMAIL API
# --------------------------------
def fetch_emails():
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", maxResults=EMAIL_LIMIT).execute()
    messages = results.get("messages", [])

    categories = {
        "Important": [],
        "Job Alerts": [],
        "From Keywords": [],
        "Other": []
    }

    keywords = ["AI", "Machine Learning", "Data Science", "Stargate"]

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        headers = msg["payload"]["headers"]
        subject = sender = date = "(Unknown)"
        
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            elif header["name"] == "From":
                sender = header["value"]
            elif header["name"] == "Date":
                date = header["value"]

        body = "(No Content)"
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break

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
# MAIN EXECUTION
# --------------------------------
if __name__ == "__main__":
    categories = fetch_emails()
    save_to_obsidian(categories)
    print("✅ Email fetching complete!")
