import os
import pickle
import base64
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage

# 📌 Define Constants
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"  # Stores OAuth token
EMAIL_FILE = "emails.txt"  # Where fetched emails are saved

def authenticate_gmail():
    """
    Authenticate the user with Gmail API using OAuth2.
    Saves credentials to `token.json` for future use.
    """
    creds = None

    # Load saved credentials if they exist
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)

    # If credentials are invalid, refresh or request new authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for future use
            with open(TOKEN_FILE, "wb") as token:
                token.write(creds.to_json().encode("utf-8"))

    return creds

def fetch_unread_emails():
    """
    Fetch unread emails from Gmail and return a list of email details.
    """
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])
    
    emails = []
    
    if not messages:
        print("📭 No new emails.")
        return emails

    print(f"📩 Fetching {len(messages)} unread emails...\n")

    for msg in messages:
        msg_id = msg["id"]
        msg_data = service.users().messages().get(userId="me", id=msg_id, format="metadata").execute()
        
        headers = msg_data.get("payload", {}).get("headers", [])
        email_from = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        email_subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

        emails.append({"from": email_from, "subject": email_subject})

    return emails

def save_emails_to_file(email_list):
    """
    Save fetched email details to a text file.
    """
    with open(EMAIL_FILE, "w", encoding="utf-8") as f:
        for email in email_list:
            f.write(f"📧 From: {email['from']}\n📜 Subject: {email['subject']}\n\n")

    print(f"✅ Fetched emails saved to {EMAIL_FILE}")

if __name__ == "__main__":
    unread_emails = fetch_unread_emails()
    
    if unread_emails:
        save_emails_to_file(unread_emails)
    else:
        print("No unread emails to save.")

    # ✅ Status messages
    if os.path.exists("token.json"):
        print("🔐 OAuth authentication complete. Token saved.")
    else:
        print("⚠️ Authentication failed. Check credentials.json.")

