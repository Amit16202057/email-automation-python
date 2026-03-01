import csv

with open("emails.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    print("Fieldnames found:", fieldnames)
    
    rows = list(reader)
    print(f"Number of rows: {len(rows)}")
    
    # Print first row
    if rows:
        print("\nFirst row:")
        print(rows[0])