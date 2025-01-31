import imapclient
import email
import os
import dotenv

# Load credentials from .env file
dotenv.load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_FOLDER = os.getenv("EMAIL_FOLDER")

def fetch_unread_emails():
    """Connects to the email server and fetches unread emails."""
    with imapclient.IMAPClient(EMAIL_SERVER) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.select_folder(EMAIL_FOLDER, readonly=True)

        # Search for unread emails
        unread_messages = server.search(["UNSEEN"])

        if not unread_messages:
            print("No unread emails found.")
            return []

        print(f"Found {len(unread_messages)} unread emails.")
        
        emails = []
        for msg_id in unread_messages:
            raw_message = server.fetch([msg_id], ["RFC822"])[msg_id][b"RFC822"]
            msg = email.message_from_bytes(raw_message)

            # Extract relevant data
            email_data = {
                "From": msg["From"],
                "Subject": msg["Subject"],
                "Date": msg["Date"],
                "Body": get_email_body(msg)
            }
            emails.append(email_data)

        return emails

def get_email_body(msg):
    """Extracts the email body (text version)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")

if __name__ == "__main__":
    unread_emails = fetch_unread_emails()
    for email in unread_emails:
        print("\n📩 **New Email**")
        print(f"From: {email['From']}")
        print(f"Subject: {email['Subject']}")
        print(f"Date: {email['Date']}")
        print(f"Body Preview: {email['Body'][:300]}...")  # Print first 300 characters
