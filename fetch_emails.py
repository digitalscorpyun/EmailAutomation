import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 🗂️ Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"  # Adjusted to OneDrive

# 🔍 Keywords to mark emails as 🔴 important
IMPORTANT_KEYWORDS = ["urgent", "action required", "important", "security alert", "warning"]


def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")  # Force refresh token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def fetch_unread_emails():
    """Fetch unread emails from Gmail."""
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    print("🔍 Testing API Response...")
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    print(f"📜 Raw API Response: {results}")  # Debugging output

    messages = results.get("messages", [])
    if not messages:
        print("📭 No unread emails found.")
        return []

    email_list = []
    for msg in messages[:10]:  # Limit to 10 emails for debugging
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
    """Save emails in Obsidian markdown format, sorted by sender."""
    os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)  # Ensure directory exists

    categorized_emails = {}
    for email in email_list:
        sender = email["from"]
        if sender not in categorized_emails:
            categorized_emails[sender] = []
        categorized_emails[sender].append(email)

    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for sender, emails in categorized_emails.items():
            f.write(f"## 📧 {sender}\n")
            for email in emails:
                f.write(f"### {email['subject']}\n")
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
