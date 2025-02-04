import imaplib
import email
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USER = "mikerkibbe73@gmail.com"
GMAIL_PASSWORD = "w00d$On!"
TO_EMAIL = "mikerkibbe73@gmail.com"  # Notification recipient
OBSIDIAN_PATH = "C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"
EMAIL_LIMIT = 10
KEYWORD = 'Python'

# Connect to Gmail IMAP server
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(GMAIL_USER, GMAIL_PASSWORD)
mail.select("inbox")

# Search for emails with the keyword in the subject
result, email_ids = mail.search(None, f'(SUBJECT "{KEYWORD}")')
email_ids = email_ids[0].split()

# Fetch latest X emails
email_entries = []
for num in email_ids[-EMAIL_LIMIT:]:
    result, msg_data = mail.fetch(num, '(RFC822)')
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            raw_email = response_part[1]
            msg = email.message_from_bytes(raw_email)

            subject = msg["Subject"] or "(No Subject)"
            sender = msg["From"] or "(Unknown Sender)"
            date = msg["Date"] or "(No Date)"
            body = ""

            # Extract email body
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            # Format email entry
            email_entry = f"### 📧 {subject}\n- **From:** {sender}\n- **Date:** {date}\n\n{body}\n---\n"
            email_entries.append(email_entry)

# Close the IMAP connection
mail.logout()

# Save to Obsidian
if email_entries:
    os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)
    with open(OBSIDIAN_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## 🗓️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n".join(email_entries))
    print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")
else:
    print("⚠️ No new emails found.")

# Send email notification
def send_email_notification(success=True):
    subject = "✅ Email Sync Successful" if success else "⚠️ Email Sync Failed"
    body = f"Email sync to Obsidian completed successfully!\nFile saved at: {OBSIDIAN_PATH}" if success else "Email sync encountered an issue."
    msg = MIMEText(body)
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")

send_email_notification(True)