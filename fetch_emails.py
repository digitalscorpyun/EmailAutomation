import os
import json
import smtplib
import ssl
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 📂 Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"

# 📧 Outlook Email Configuration
OUTLOOK_EMAIL = "mikekibbe73@outlook.com"
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD")  # Securely stored in environment variable
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

# 🔍 Important Senders & Keywords for Filtering
IMPORTANT_SENDERS = {
    "jobalerts-noreply@linkedin.com": "💼 Job Alerts",
    "breakingnews@nytimes.com": "📰 Breaking News",
}
IMPORTANT_KEYWORDS = {
    "Intellisearch", "Help Desk Analyst", "Robert Half", "hiring",
    "Atomwaffen Division", "BRICS", "Claudia Sheinbaum", "Daniel Dale",
    "DEI revolution", "Dr. Greg Carr", "@AfricanaCarr", "Alex Padilla",
    "Howard French", "Sheikh Tahnoun bin Zayed al Nahyan", "Stargate",
    "Vera C. Rubin Observatory", "Wharf Jérémie"
}

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
    """Fetch unread emails from Gmail, categorize, and filter them."""
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])

    categorized_emails = {
        "📌 Important Emails": [], "📢 Breaking News": [],
        "💼 Job Alerts": [], "✉️ General Emails": []
    }
    notification_emails = []

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date_received = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

        # Categorization based on senders or keywords
        category = "✉️ General Emails"
        for keyword in IMPORTANT_KEYWORDS:
            if keyword.lower() in subject.lower():
                category = "📢 Breaking News"
                break
        for key, value in IMPORTANT_SENDERS.items():
            if key in sender:
                category = value
                break

        # Append email data
        email_entry = {"from": sender, "subject": subject, "date": date_received}
        categorized_emails[category].append(email_entry)

        # Track important emails for notification
        if category != "✉️ General Emails":
            notification_emails.append(email_entry)

    return categorized_emails, notification_emails

def save_to_obsidian(email_categories):
    """Save categorized emails in Obsidian markdown format."""
    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for category, emails in email_categories.items():
            f.write(f"## {category}\n\n")
            for email in emails:
                f.write(f"### {email['subject']}\n")
                f.write(f"**From:** {email['from']}\n")
                f.write(f"**Received:** {email['date']}\n\n")
                f.write("---\n")
    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")

def send_outlook_notification(emails):
    """Send an email notification for filtered important emails."""
    if not emails:
        return  # No important emails to notify

    try:
        message = EmailMessage()
        message["Subject"] = "🚀 Important Gmail Updates"
        message["From"] = OUTLOOK_EMAIL
        message["To"] = OUTLOOK_EMAIL

        body = "# 🚀 Important Emails Found\n\n"
        for email in emails:
            body += f"- **{email['subject']}**\n"
            body += f"  📧 From: {email['from']}\n"
            body += f"  📅 Received: {email['date']}\n\n"
        message.set_content(body)

        # Send email via Outlook SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
            server.send_message(message)
        
        print("📧 Notification email sent successfully.")
    
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")

if __name__ == "__main__":
    print("📩 Fetching unread emails...")
    categorized_emails, notification_emails = fetch_unread_emails()
    
    if any(categorized_emails.values()):
        save_to_obsidian(categorized_emails)
        send_outlook_notification(notification_emails)
        print("✅ Email fetching complete!")
    else:
        print("📭 No matching emails found.")
