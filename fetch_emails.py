import smtplib
from email.mime.text import MIMEText

# Gmail SMTP Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USER = "mikerkibbe73@gmail.com"
GMAIL_PASSWORD = "ch0c0l@te!"  # Use your App Password

# Recipient Email
TO_EMAIL = "mikerkibbe73@gmail.com"

def send_email_notification():
    subject = "✅ Test Email Notification"
    body = "This is a test email notification to confirm Gmail SMTP is working."

    msg = MIMEText(body)
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    try:
        print("📧 Sending email notification...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")

if __name__ == "__main__":
    send_email_notification()
