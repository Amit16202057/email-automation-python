import csv
import smtplib
import time
import os
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ---------- LOAD ENV (Python 3.12 safe) ----------
load_dotenv(dotenv_path=".env")

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

CSV_FILE = "emails.csv"
LOG_FILE = "send_log.txt"

# ---------- LOAD HTML TEMPLATE ----------
with open("email_template.html", "r", encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

# ---------- SETTINGS (YOU CAN CHANGE THESE) ----------
CHECK_INTERVAL = 300        # 5 minutes
EMAIL_DELAY = 30            # 30 seconds between emails
DAILY_LIMIT = 100           # max emails per day

SUBJECT = "Business Introduction – SR Shipping Group"

# ---------- HELPERS ----------
def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

def send_email(to_email, name, company):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = SUBJECT

    body = HTML_TEMPLATE.replace("{{name}}", name).replace("{{company}}", company)
    msg.attach(MIMEText(body, "html"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

def get_today_sent_count():
    if not os.path.exists(LOG_FILE):
        return 0

    today = date.today().isoformat()
    count = 0

    with open(LOG_FILE) as f:
        for line in f:
            if today in line and "SENT" in line:
                count += 1

    return count

# ---------- MAIN LOOP ----------
print("🚀 Email automation started...")
log("SYSTEM STARTED")

while True:
    sent_today = get_today_sent_count()

    if sent_today >= DAILY_LIMIT:
        print("⛔ Daily limit reached. Sleeping until next check...")
        time.sleep(CHECK_INTERVAL)
        continue

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    updated = False

    for row in rows:
        if row["sent"] == "NO":
            if sent_today >= DAILY_LIMIT:
                break

            try:
                send_email(row["email"], row["name"], row["company"])
                row["sent"] = "YES"
                sent_today += 1

                log(f"SENT -> {row['email']}")
                print(f"✅ Sent to {row['email']}")

                time.sleep(EMAIL_DELAY)

                updated = True

            except Exception as e:
                log(f"ERROR -> {row['email']} -> {e}")
                print(f"❌ Error sending to {row['email']}")

    if updated:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    time.sleep(CHECK_INTERVAL)
