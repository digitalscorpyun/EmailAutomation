import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔑 OAuth & Gmail API Setup
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# 📂 Path to Obsidian Inbox
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"

# 📧 Email Notification Settings
SMTP_SERVER = "smtp.office365.com"  # Outlook SMTP
SMTP_PORT = 587
OUTLOOK_EMAIL = "mikekibbe73@outlook.com"  # Your personal email
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD")  # ⚠️ Store this securely in an env variable!

# 🔍 Important Categories
IMPORTANT_SENDERS = {
    "jobalerts-noreply@linkedin.com": "💼 Job Alerts",
}

# 🎯 Important Keywords
IMPORTANT_KEYWORDS = {
    "Intellisearch", "Help Desk Analyst", "Robert Half", "hiring", "Atomwaffen Division",
    "BRICS", "Claudia Sheinbaum", "Daniel Dale", "DEI revolution", "Dr. Greg Carr",
    "@AfricanaCarr", "Alex Padilla", "Howard French", "Sheikh Tahnoun bin Zayed al Nahyan",
    "Stargate", "Vera C. Rubin Observatory", "Wharf Jérémie"
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

def send_email_notification(email_details):
    """Send an email notification via Outlook for high-priority emails."""
    try:
        msg = MIMEMultipart()
        msg["From"] = OUTLOOK_EMAIL
        msg["To"] = OUTLOOK_EMAIL
        msg["Subject"] = f"🚨 Important Email Alert: {email_details['subject']}"
        
        email_body = f"""
        <h2>🚨 Important Email Alert</h2>
        <p><strong>From:</strong> {email_details['from']}</p>
        <p><strong>Received:</strong> {email_details['date']}</p>
        <p><strong>Subject:</strong> {email_details['subject']}</p>
        <p><strong>🔗 <a href="https://mail.google.com/mail/u/0/#inbox/{email_details['id']}">View Email in Gmail</a></strong></p>
        """

        msg.attach(MIMEText(email_body, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
        server.sendmail(OUTLOOK_EMAIL, OUTLOOK_EMAIL, msg.as_string())
        server.quit()

        print(f"📧 Notification sent for: {email_details['subject']}")
    except Exception as e:
        print(f"⚠️ Email notification failed: {str(e)}")

def fetch_unread_emails():
    """Fetch unread emails from Gmail, apply keyword filtering, and categorize them."""
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])

    categorized_emails = {
        "📌 Important Emails": [],
        "📢 Breaking News": [],
        "💼 Job Alerts": [],
        "✉️ General Emails": []
    }
    unique_senders = set()

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date_received = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

        unique_senders.add(sender)  # Collect sender for summary list

        # Categorization based on senders and keywords
        category = "✉️ General Emails"
        should_notify = False  # Flag for email notification
        for keyword in IMPORTANT_KEYWORDS:
            if keyword.lower() in subject.lower():
                category = "📢 Breaking News"
                should_notify = True
                break
        for key, value in IMPORTANT_SENDERS.items():
            if key in sender:
                category = value
                break

        email_details = {
            "from": sender,
            "subject": subject,
            "date": date_received,
            "id": msg["id"]  # Needed for Gmail direct link
        }

        categorized_emails[category].append(email_details)

        # 📧 Send email notification if important keyword is found
        if should_notify:
            send_email_notification(email_details)

        # ✅ Mark email as read after processing
        service.users().messages().modify(userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}).execute()

    return categorized_emails, sorted(unique_senders)

def save_to_obsidian(email_categories, senders_list):
    """Save categorized emails and sender list in Obsidian markdown format."""
    with open(OBSIDIAN_PATH, "w", encoding="utf-8") as f:
        f.write("# 📩 Email Summaries\n\n")
        for category, emails in email_categories.items():
            f.write(f"## 🔹 {category}\n\n")
            for email in emails:
                f.write(f"📧 **From:** {email['from']}\n")
                f.write(f"📅 **Received:** {email['date']}\n")
                f.write(f"📝 **Summary:** {email['subject']}\n\n")
                f.write("---\n")
        
        # 📜 Add Bulleted List of Unique Senders
        f.write("\n## 🔹 Email Senders\n\n")
        for sender in senders_list:
            f.write(f"- {sender}\n")

    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")

if __name__ == "__main__":
    print("📩 Fetching unread emails...")
    categorized_emails, unique_senders = fetch_unread_emails()
    if any(categorized_emails.values()):
        save_to_obsidian(categorized_emails, unique_senders)
        print("✅ Email fetching complete!")
    else:
        print("📭 No matching emails found.")
