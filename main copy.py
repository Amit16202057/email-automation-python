import csv
import smtplib
import time
import os
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# =============================
# LOAD ENVIRONMENT VARIABLES
# =============================
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

CSV_FILE = "emails.csv"
LOG_FILE = "send_log.txt"

EMAIL_DELAY = 5          # seconds between emails
DAILY_LIMIT = 800        # change if needed
START_FROM =  972        # start from email #71 (index begins at 0)

SUBJECT = "Cooperation Opportunity for Chittagong & Dhaka Shipments - S.R.Shipping Agency Bangladesh!✨"

# =============================
# LOAD HTML TEMPLATE
# =============================
with open("email_template.html", "r", encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

# =============================
# LOG FUNCTION
# =============================
def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

# =============================
# SEND EMAIL FUNCTION
# =============================
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

# =============================
# COUNT TODAY SENT EMAILS
# =============================
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

# =============================
# START SCRIPT
# =============================
print("🚀 Email automation started")

sent_today = get_today_sent_count()

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# =============================
# MAIN LOOP
# =============================
for i, row in enumerate(rows):

    # Skip already processed rows
    if i < START_FROM:
        continue

    if row["sent"] == "NO":

        if sent_today >= DAILY_LIMIT:
            print("⚠ Daily sending limit reached")
            break

        try:
            send_email(row["email"], row["name"], row["company"])

            row["sent"] = "YES"
            sent_today += 1

            log(f"SENT -> {row['email']}")
            print(f"✅ Sent to {row['email']}")

            # ===== SAVE IMMEDIATELY (CRASH SAFE) =====
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            time.sleep(EMAIL_DELAY)

        except Exception as e:
            log(f"ERROR -> {row['email']} -> {e}")
            print(f"❌ Error sending to {row['email']} -> {e}")

print("✅ Job finished")
