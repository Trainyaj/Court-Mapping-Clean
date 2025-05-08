import csv

with open("dockets-2025-04-30.csv", "r", encoding="utf-8", errors="replace") as infile, \
     open("dockets_cleaned.csv", "w", encoding="utf-8", newline="") as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        # Remove stray unescaped quotes and trim rows
        cleaned_row = [field.replace('"', '""').strip() for field in row]
        if len(cleaned_row) >= 52:
            writer.writerow(cleaned_row[:52])  # truncate extras
        else:
            writer.writerow(cleaned_row + [''] * (52 - len(cleaned_row)))  # pad missing