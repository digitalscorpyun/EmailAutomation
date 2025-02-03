import imaplib
import email
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --------------------------------
# CONFIGURATION (GMAIL ONLY)
# --------------------------------

# Gmail IMAP Settings (For Fetching Emails)
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
GMAIL_USER = "mikerkibbe73@gmail.com"
GMAIL_PASSWORD = "w00d$On!"  # Use your Gmail password 

# Gmail SMTP Settings (For Sending Notifications)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
TO_EMAIL = "mikerkibbe73@gmail.com"  # Self-notifications

# Obsidian File Path
OBSIDIAN_PATH = r"C:/Users/miker/OneDrive/Documents/Knowledge Hub/Inbox/Emails.md"

# Number of emails to fetch
EMAIL_LIMIT = 10  # Adjust as needed

# --------------------------------
# FETCH EMAILS FROM GMAIL
# --------------------------------
def fetch_emails():
    try:
        print("🔄 Connecting to Gmail IMAP server...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        mail.select("inbox")

        # Search for all emails
        result, data = mail.search(None, "ALL")
        email_ids = data[0].split()[-EMAIL_LIMIT:]  # Fetch latest X emails

        email_entries = []
        for num in email_ids:
            result, msg_data = mail.fetch(num, "(RFC822)")
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

        mail.logout()
        return email_entries

    except Exception as e:
        print(f"⚠️ Error fetching emails: {e}")
        return []

# --------------------------------
# SAVE TO OBSIDIAN
# --------------------------------
def save_to_obsidian(emails):
    try:
        if not emails:
            print("⚠️ No new emails found.")
            return False

        os.makedirs(os.path.dirname(OBSIDIAN_PATH), exist_ok=True)

        with open(OBSIDIAN_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n## 🗓️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n".join(emails))
        
        print(f"✅ Emails synced to Obsidian at {OBSIDIAN_PATH}")
        return True

    except Exception as e:
        print(f"⚠️ Error saving to Obsidian: {e}")
        return False

# --------------------------------
# SEND EMAIL NOTIFICATION
# --------------------------------
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

# --------------------------------
# MAIN EXECUTION
# --------------------------------
if __name__ == "__main__":
    emails = fetch_emails()
    success = save_to_obsidian(emails)
    send_email_notification(success)
    print("✅ Email fetching complete!")
