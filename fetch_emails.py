import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 📂 Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"

# 🚫 Blocked Senders (Emails from these will be ignored)
BLOCKED_SENDERS = {
    "notification@service.tiktok.com",
    "no-reply@facebook.com",
    "updates@twitter.com"
}

# ✅ Important Senders (Emails from these will be prioritized)
IMPORTANT_SENDERS = {
    "jobalerts-noreply@linkedin.com": "💼 Job Alerts",
    "editor@newyorker.com": "📰 Breaking News"
}

# 🔍 Important Keywords (Only fetch emails containing these words)
IMPORTANT_KEYWORDS = {"urgent", "breaking", "action required", "opportunity", "job"}

# 🔢 Limit the number of emails fetched
EMAIL_FETCH_LIMIT = 20  # Change this to the desired number of emails to process

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def fetch_unread_emails():
    """Fetch unread emails from Gmail and apply filters."""
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    # Fetch only unread emails with a limit
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], q="is:unread", maxResults=EMAIL_FETCH_LIMIT
    ).execute()
    messages = results.get("messages", [])

    categorized_emails = {"💼 Job Alerts": [], "📰 Breaking News": [], "📌 Important Emails": [], "✉️ General Emails": []}

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date_received = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

        # 🚫 Skip blocked senders
        if any(blocked in sender for blocked in BLOCKED_SENDERS):
            print(f"🚫 Skipping email from {sender} (Blocked Sender)")
            continue
        
        # 🔍 Filter by keywords (Skip emails that don’t contain important keywords)
        if not any(keyword.lower() in subject.lower() for keyword in IMPORTANT_KEYWORDS):
            print(f"⚠️ Skipping email: {subject} (No matching keywords)")
            continue

        # Categorization
        category = "✉️ General Emails"
        for key, value in IMPORTANT_SENDERS.items():
            if key in sender:
                category = value
                break
        for keyword in IMPORTANT_KEYWORDS:
            if keyword.lower() in subject.lower():
                category = "📰 Breaking News"
                break
        
        categorized_emails[category].append({
            "from": sender,
            "subject": subject,
            "date": date_received
        })

        # Mark email as read
        service.users().messages().modify(userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}).execute()

    return categorized_emails

def save_to_obsidian(email_categories):
    """Save categorized emails in Obsidian markdown format with better structure."""
    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for category, emails in email_categories.items():
            if emails:
                f.write(f"## 🔹 {category}\n\n")
                for email in emails:
                    f.write(f"**📧 From:** {email['from']}\n")
                    f.write(f"**📅 Received:** {email['date']}\n")
                    f.write(f"**📝 Summary:** {email['subject']}\n")
                    f.write(f"🔗 [View Full Email](#)\n\n")
                    f.write("---\n\n")
    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")

if __name__ == "__main__":
    print("📩 Fetching unread emails...")
    categorized_emails = fetch_unread_emails()
    if any(categorized_emails.values()):
        save_to_obsidian(categorized_emails)
        print("✅ Email fetching complete!")
    else:
        print("📭 No matching emails found.")
