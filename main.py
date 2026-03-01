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
DAILY_LIMIT = 1500        # change if needed
START_FROM =  0          # start from beginning

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
    with open(LOG_FILE, "a", encoding="utf-8") as f:
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

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            if today in line and "SENT" in line:
                count += 1

    return count

# =============================
# CLEAN ROW FUNCTION
# =============================
def clean_row(row, fieldnames):
    """Remove any None keys and ensure only valid fieldnames"""
    cleaned = {}
    for field in fieldnames:
        if field is not None:  # Skip None fieldnames
            value = row.get(field, "")
            cleaned[field] = value if value is not None else ""
    return cleaned

# =============================
# START SCRIPT
# =============================
print("🚀 Email automation started")

sent_today = get_today_sent_count()

# Read CSV with explicit fieldnames to avoid issues
with open(CSV_FILE, newline="", encoding="utf-8") as f:
    # Read all lines to check format
    lines = f.readlines()
    print(f"CSV has {len(lines)} lines")
    
    # Reset file pointer
    f.seek(0)
    
    # Try reading with DictReader
    try:
        # First, detect if there are any BOM characters or weird formatting
        first_line = f.readline().strip()
        f.seek(0)
        
        if first_line and first_line.startswith('\ufeff'):
            print("⚠ BOM detected in CSV, skipping...")
            # Skip BOM character
            f.read(1)
        
        reader = csv.DictReader(f)
        raw_fieldnames = reader.fieldnames
        print(f"Detected raw fieldnames: {raw_fieldnames}")
        
        # Clean fieldnames - remove None and strip whitespace
        fieldnames = []
        for fn in raw_fieldnames:
            if fn is not None and fn.strip():
                fieldnames.append(fn.strip())
        
        if not fieldnames:
            print("⚠ No valid headers found, using default headers")
            fieldnames = ["sent", "email", "name", "company"]
            f.seek(0)
            # Skip first line if it exists
            f.readline()
            reader = csv.DictReader(f, fieldnames=fieldnames)
        else:
            # Reset and read again with cleaned fieldnames
            f.seek(0)
            reader = csv.DictReader(f)
        
        print(f"Using fieldnames: {fieldnames}")
        
        # Read all rows and clean them
        rows = []
        for row in reader:
            cleaned_row = clean_row(row, fieldnames)
            rows.append(cleaned_row)
            
        print(f"Successfully read {len(rows)} rows")
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        print("Creating new CSV structure...")
        fieldnames = ["sent", "email", "name", "company"]
        rows = []

# =============================
# MAIN LOOP
# =============================
for i, row in enumerate(rows):
    # Skip already processed rows
    if i < START_FROM:
        continue

    # Safely get sent status
    sent_status = row.get("sent", "NO")
    if sent_status is None:
        sent_status = "NO"
    
    if sent_status == "NO":
        if sent_today >= DAILY_LIMIT:
            print("⚠ Daily sending limit reached")
            break

        try:
            email = row.get("email", "").strip() if row.get("email") else ""
            name = row.get("name", "").strip() if row.get("name") else "management"
            company = row.get("company", "").strip() if row.get("company") else "(your company)"
            
            if not email:
                print(f"⚠ Skipping row {i}: No email address")
                continue
            
            print(f"Attempting to send to: {email}")
            send_email(email, name, company)

            row["sent"] = "YES"
            sent_today += 1

            log(f"SENT -> {email}")
            print(f"✅ Sent to {email}")

            # ===== SAVE IMMEDIATELY =====
            try:
                with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Clean all rows before writing
                    clean_rows = []
                    for r in rows:
                        clean_r = clean_row(r, fieldnames)
                        clean_rows.append(clean_r)
                    
                    writer.writerows(clean_rows)
                print(f"✓ Saved progress to CSV")
            except Exception as save_error:
                log(f"ERROR SAVING CSV -> {save_error}")
                print(f"❌ Error saving CSV: {save_error}")
                # Print more details about the error
                import traceback
                traceback.print_exc()

            time.sleep(EMAIL_DELAY)

        except Exception as e:
            log(f"ERROR -> {row.get('email', 'unknown')} -> {e}")
            print(f"❌ Error sending to {row.get('email', 'unknown')} -> {e}")
            # Print more details about the error
            import traceback
            traceback.print_exc()

print("✅ Job finished")