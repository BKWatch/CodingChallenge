import csv 
import sys

# Function to parse TSV file
def parse_tsv(file_path):
    addresses = []
    organizations = set(["llc", "inc.", "pvt.", "ltd."])
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tsv_reader = csv.DictReader(file, delimiter="\t")
            for row in tsv_reader:
                address_entry = {}
                
                # Process names and check for company names in the 'last' field
                first_name = row.get("first", "").strip()
                middle_name = "" if row.get("middle") in ["N/M/N", None] else row.get("middle").strip()
                last_name = row.get("last", "").strip()

                # Detect organization names in the 'last' name field
                if any(keyword in last_name.lower() for keyword in organizations):
                    address_entry["organization"] = last_name
                    last_name = ""

                # Compile full name if not purely an organization
                full_name = " ".join(filter(None, [first_name, middle_name, last_name])).strip()
                if full_name:
                    address_entry["name"] = full_name

                # Organization field handling
                if row.get("organization") not in ["N/A", None]:
                    address_entry["organization"] = row["organization"].strip()

                # Address components
                address_entry.update({
                    "street": row.get("address", "").strip(),
                    "city": row.get("city", "").strip(),
                    "county": row.get("county", "").strip(),
                    "state": row.get("state", "").strip()
                })

                # Handle ZIP and optional ZIP+4
                zip_code = row.get("zip", "").strip()
                zip4 = row.get("zip4", "").strip()
                address_entry["zip"] = f"{zip_code}-{zip4}" if zip4 else zip_code

                addresses.append(address_entry)

    except Exception as error:
        sys.stderr.write(f"Error parsing TSV file at {filepath}: {error}\n")
        sys.exit(1)

    return addresses