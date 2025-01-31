import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email import message_from_bytes
import base64
import datetime

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 📂 Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"  # Adjusted to your correct vault

# 🔍 Keywords to mark emails as 🔴 Important
IMPORTANT_KEYWORDS = ["urgent", "action required", "important", "security alert", "warning"]

# 📌 Email Categories
CATEGORIES = {
    "Job Leads": ["linkedin", "indeed", "glassdoor", "job alert"],
    "Breaking News": ["cnn", "nytimes", "washingtonpost", "breaking", "alert"],
    "Tech Updates": ["github", "stack overflow", "tech news"],
    "Promotions & Deals": ["sale", "discount", "offer", "coupon", "deal"],
    "Personal": ["friend", "family", "invitation", "meetup"],
}

# ✅ **Approved Senders (Only emails from these senders will be processed)**
APPROVED_SENDERS = [
    "jobs@linkedin.com",
    "alerts@cnn.com",
    "no-reply@github.com",
    "security@google.com"
]

# ✅ **Required Keywords (Only emails containing these will be processed)**
REQUIRED_KEYWORDS = [
    "job opportunity",
    "security alert",
    "urgent",
    "AI update"
]


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


def categorize_email(subject, sender):
    """Categorize emails based on sender or subject."""
    subject_lower = subject.lower()
    sender_lower = sender.lower()

    for category, keywords in CATEGORIES.items():
        if any(keyword in subject_lower or keyword in sender_lower for keyword in keywords):
            return category

    return "Other"


def is_valid_email(sender, subject, body):
    """Check if the email meets the criteria to be saved."""
    sender = sender.lower()
    
    # ✅ Check if sender is approved
    if not any(approved in sender for approved in APPROVED_SENDERS):
        return False  # Ignore emails from unapproved senders
    
    # ✅ Check if email contains any required keyword
    subject_body = f"{subject.lower()} {body.lower()}"
    if not any(keyword in subject_body for keyword in REQUIRED_KEYWORDS):
        return False  # Ignore emails that do not contain any required keyword
    
    return True


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

        # Decode email body if available
        body = "No preview available."
        if "parts" in msg_data["payload"]:
            parts = msg_data["payload"]["parts"]
            for part in parts:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    body = body[:500] + "..." if len(body) > 500 else body  # Limit preview to 500 chars
                    break

        # ❌ Filter out emails that don’t meet criteria
        if not is_valid_email(sender, subject, body):
            continue

        # 🔍 Mark important emails
        importance = "🟢"  # Default to normal
        if any(keyword.lower() in subject.lower() for keyword in IMPORTANT_KEYWORDS):
            importance = "🔴"  # Mark as important

        category = categorize_email(subject, sender)

        email_list.append({
            "from": sender,
            "subject": f"{importance} {subject}",
            "date": date_received,
            "category": category,
            "body": body
        })

    # Sort emails by latest date
    return sorted(email_list, key=lambda x: x["date"], reverse=True)


def save_to_obsidian(email_list):
    """Save emails in Obsidian markdown format grouped by category."""
    emails_by_category = {}

    for email in email_list:
        category = email["category"]
        if category not in emails_by_category:
            emails_by_category[category] = []
        emails_by_category[category].append(email)

    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for category, emails in emails_by_category.items():
            f.write(f"## 📌 {category}\n\n")
            for email in emails:
                f.write(f"### {email['subject']}\n")
                f.write(f"**From:** {email['from']}\n")
                f.write(f"**Received:** {email['date']}\n")
                f.write(f"**Preview:** {email['body']}\n")
                f.write(f"---\n\n")

    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")


if __name__ == "__main__":
    print("📩 Fetching unread emails...")
    unread_emails = fetch_unread_emails()
    if unread_emails:
        save_to_obsidian(unread_emails)
        print("✅ Email fetching complete!")
    else:
        print("📭 No matching emails found.")
