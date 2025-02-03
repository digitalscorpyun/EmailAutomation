import os
import base64
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --------------------------------
# CONFIGURATION
# --------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"  # Stores OAuth2 tokens
CREDENTIALS_FILE = "credentials.json"  # OAuth2 credentials file

# --------------------------------
# AUTHENTICATE WITH GMAIL
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
# FETCH EMAILS
# --------------------------------
def fetch_emails():
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])

    email_entries = []
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "(No Date)")

        body = ""
        if "data" in msg_data["payload"]["body"]:
            body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8", errors="ignore")

        email_entry = f"### 📧 {subject}\n- **From:** {sender}\n- **Date:** {date}\n\n{body}\n---\n"
        email_entries.append(email_entry)

    return email_entries

# --------------------------------
# MAIN EXECUTION
# --------------------------------
if __name__ == "__main__":
    emails = fetch_emails()
    if emails:
        print("\n".join(emails))
    else:
        print("⚠️ No new emails found.")
