import os
import base64
import json
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the Gmail API scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Path to the credentials JSON file
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.pickle"

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2 and return the service object."""
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, log in and create a new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def fetch_unread_emails():
    """Fetch unread emails from Gmail."""
    service = authenticate_gmail()

    # Get unread emails
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])

    if not messages:
        print("No unread emails found.")
        return

    print(f"Found {len(messages)} unread emails:\n")

    # Retrieve email details
    for msg in messages[:5]:  # Limit to 5 emails for now
        msg_id = msg["id"]
        msg_data = service.users().messages().get(userId="me", id=msg_id).execute()
        headers = msg_data["payload"]["headers"]

        subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
        sender = next((header["value"] for header in headers if header["name"] == "From"), "Unknown Sender")

        print(f"📧 From: {sender}\n   Subject: {subject}\n   ID: {msg_id}\n")

if __name__ == "__main__":
    fetch_unread_emails()
