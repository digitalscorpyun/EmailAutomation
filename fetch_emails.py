import os
import json
import base64
import datetime
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --------------------------------
# CONFIGURATION
# --------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
OBSIDIAN_PATH = r"C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"
EMAIL_LIMIT = 10  # Number of emails to fetch
MAX_BODY_LENGTH = 600  # Limit email body preview length

# --------------------------------
# AUTHENTICATE GMAIL API
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
# FETCH EMAILS FROM GMAIL
# --------------------------------
def fetch_emails():
    try:
        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=EMAIL_LIMIT).execute()
        messages = results.get("messages", [])

        email_entries = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            payload = msg_data["payload"]
            headers = payload["headers"]

            subject = sender = date = "(Unknown)"
            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Date":
                    date = header["value"]

            # Extract email body (if available)
            body = "(No email body found)"
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                        break

            # Remove tracking links and unsubscribe links
            body = re.sub(r'https?://\S+', '', body)  # Remove URLs
            body = re.sub(r'Unsubscribe.*', '', body, flags=re.IGNORECASE)  # Remove unsubscribe text

            # Trim body if too long
            if len(body) > MAX_BODY_LENGTH:
                body = body[:MAX_BODY_LENGTH] + "...\n\n[Read More in Gmail]"

            # Format email entry with a collapsible section
            email_entry = (
                f"## 📬 {subject}\n"
                f"- **📧 From:** {sender}\n"
                f"- **📅 Date:** {date}\n\n"
                f"### 📜 Email Content\n"
                f"<details>\n"
                f"  <summary>Click to expand</summary>\n\n"
                f"  {body}\n\n"
                f"</details>\n\n"
                f"---\n"
            )
            email_entries.append(email_entry)

        return email_entries

    except Exception as e:
        print(f"⚠️ Error fetching emails: {e}")
        return []

# --------------------------------
# SAVE TO OBSIDIAN WITH TIMESTAMP
# --------------------------------
def save_to_obsidian(emails):
    try:
        if not emails:
            print("⚠️ No new emails found.")
            return False

        os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(OBSIDIAN_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n# 📬 Email Sync Log ({timestamp})\n\n")
            f.write("\n".join(emails))
        
        print(f"✅ Emails successfully saved to Obsidian: {OBSIDIAN_PATH}")
        return True

    except Exception as e:
        print(f"⚠️ Error saving to Obsidian: {e}")
        return False

# --------------------------------
# MAIN EXECUTION
# --------------------------------
if __name__ == "__main__":
    emails = fetch_emails()
    success = save_to_obsidian(emails)
    print("✅ Email fetching complete!")
