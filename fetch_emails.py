import os
import pickle
import base64
import json
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"

def authenticate_gmail():
    """Authenticate user with OAuth2 and handle token refreshing."""
    creds = None

    # Load saved token if it exists
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Refresh the token if it's expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("[✅] Token refreshed successfully!")
        except Exception as e:
            print(f"[❌] Failed to refresh token: {e}")
            creds = None

    # If there are no (valid) credentials available, prompt user to log in
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
            print("[✅] Token saved successfully!")

    return creds

def fetch_unread_emails():
    """Fetch unread emails from Gmail"""
    creds = authenticate_gmail()
    
    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
        messages = results.get("messages", [])

        if not messages:
            print("[📭] No unread emails found.")
            return

        print(f"[📩] You have {len(messages)} unread emails.")

        for msg in messages:
            msg_id = msg["id"]
            message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            
            # Extract email details
            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            
            print(f"\n📧 **From:** {sender}\n📜 **Subject:** {subject}")

    except HttpError as error:
        print(f"[❌] An error occurred: {error}")

if __name__ == "__main__":
    fetch_unread_emails()
