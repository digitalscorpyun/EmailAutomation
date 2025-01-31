import os
import pickle
import base64
import re
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email import message_from_bytes

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 🗂️ Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/Knowledge Hub/Inbox/Emails.md"  # Adjust path

# 🔍 Keywords to mark emails as 🔴 important
IMPORTANT_KEYWORDS = ["urgent", "action required", "important", "security alert", "warning"]

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/gmail.readonly"],
)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")  # Force refresh token
port=0
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def fetch_unread_emails():
    """Fetch unread emails from Gmail."""
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])

    email_list = []
    for msg in messages[:100]:  # Limit to 100 unread emails
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date_received = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

        # 🔍 Mark important emails
        importance = "🟢"  # Default to normal
        if any(keyword.lower() in subject.lower() for keyword in IMPORTANT_KEYWORDS):
            importance = "🔴"  # Mark as important

        email_list.append({
            "from": sender,
            "subject": f"{importance} {subject}",
            "date": date_received
        })

    return email_list

def save_to_obsidian(email_list):
    """Save emails in Obsidian markdown format."""
    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for email in email_list:
            f.write(f"## {email['subject']}\n")
            f.write(f"**From:** {email['from']}\n")
            f.write(f"**Received:** {email['date']}\n")
            f.write(f"---\n")
    
    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")

if __name__ == "__main__":
    print("📩 Fetching unread emails...")
    unread_emails = fetch_unread_emails()
    if unread_emails:
        save_to_obsidian(unread_emails)
        print("✅ Email fetching complete!")
    else:
        print("📭 No unread emails found.")
