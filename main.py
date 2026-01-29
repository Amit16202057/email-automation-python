import csv
import smtplib
import time
import os
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------- ENV VARIABLES (FROM RENDER) ----------
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

CSV_FILE = "emails.csv"
LOG_FILE = "send_log.txt"

# ---------- SETTINGS ----------
EMAIL_DELAY = 30      # seconds between emails
DAILY_LIMIT = 150      # safe limit for Render + SMTP

SUBJECT = "Business Introduction – S.R. Shipping Agency"

# ---------- LOAD HTML TEMPLATE ----------
with open("email_template.html", "r", encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

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

# ---------- MAIN (RUN ONCE – RENDER SAFE) ----------
print("🚀 Render email job started")
log("RENDER JOB STARTED")

sent_today = get_today_sent_count()

if sent_today >= DAILY_LIMIT:
    print("⛔ Daily limit already reached")
    log("DAILY LIMIT REACHED")
    exit()

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

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

# ---------- SAVE CSV ----------
if updated:
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

log("RENDER JOB FINISHED")
print("✅ Render job completed")
