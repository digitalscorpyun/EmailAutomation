# Fetch Emails Script for Gmail Automation

## Overview
This script automates email retrieval from Gmail using **OAuth2 authentication**. It fetches unread emails and saves them into **text and CSV formats** for easy access.

---

## 🔧 Setup

### 1️⃣ Install Required Packages
Run this command in PowerShell:
```powershell
pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2️⃣ Move Credentials File
Ensure `credentials.json` is placed in the **EmailAutomation** folder:
```powershell
Move-Item -Path "C:\Users\miker\Downloads\credentials.json" -Destination "C:\Users\miker\EmailAutomation\credentials.json"
```

### 3️⃣ Run the Script
```powershell
python fetch_emails.py
```

---

## 📝 Full Script (`fetch_emails.py`)
```python
import os
import pickle
import base64
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API Scope for reading emails
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# File paths
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
EMAIL_TEXT_FILE = "emails.txt"
EMAIL_CSV_FILE = "emails.csv"

def authenticate_gmail():
    """Authenticate and return the Gmail API service using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)

def fetch_unread_emails():
    """Fetch unread emails from Gmail inbox."""
    service = authenticate_gmail()
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])
    email_list = []
    if not messages:
        print("No unread emails found.")
        return email_list
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        email_from = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        email_subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        email_list.append({"from": email_from, "subject": email_subject})
    return email_list

def save_emails_to_file(email_list):
    """Save fetched emails to a text file."""
    with open(EMAIL_TEXT_FILE, "w", encoding="utf-8") as f:
        for email in email_list:
            f.write(f"📧 From: {email['from']}\n📜 Subject: {email['subject']}\n\n")
    print(f"📄 Emails saved to {EMAIL_TEXT_FILE}")

def save_emails_to_csv(email_list):
    """Save fetched emails to a CSV file."""
    with open(EMAIL_CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["From", "Subject"])
        for email in email_list:
            writer.writerow([email["from"], email["subject"]])
    print(f"📊 Emails saved to {EMAIL_CSV_FILE}")

if __name__ == "__main__":
    emails = fetch_unread_emails()
    if emails:
        save_emails_to_file(emails)
        save_emails_to_csv(emails)
    else:
        print("📭 No new unread emails.")
```

---

## 📌 Next Steps

### 4️⃣ Verify Saved Emails
- Open the text file:
  ```powershell
  notepad emails.txt
  ```
- Open the CSV file:
  ```powershell
  start excel emails.csv
  ```

### 5️⃣ Confirm Token is Saved
```powershell
Get-ChildItem -Path "C:\Users\miker\EmailAutomation" -Filter "token.json"
```
- If `token.json` exists, OAuth authentication is working, and you won’t need to log in again. 🎉

### 6️⃣ Push Changes to GitHub
```powershell
git add fetch_emails.py
git commit -m "Updated fetch_emails.py with OAuth2 automation"
git push origin main
```

---

This is now fully automated and stored in Obsidian for reference. 🚀 Let me know if you need modifications!

