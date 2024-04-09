"""
Script: challenge.py
Purpose: Parse and combine address files (XML, TSV, plain text) into a JSON
list.
Usage: python challenge.py <file_paths>
"""

import json
import sys
import argparse
import xml.etree.ElementTree as ET
import csv
import re
import os


# Returns list of dictionaries filled with properties
def parse_xml(file_path):
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for ent in root.findall("./ENTITY/ENT"):
            record = {}

            # Find elements
            name = ent.find("NAME")
            company = ent.find("COMPANY")
            street = ent.find("STREET")
            city = ent.find("CITY")
            state = ent.find("STATE")
            zip_code = ent.find("POSTAL_CODE")

            # Process and assign if not None and not empty
            if name is not None and name.text.strip():
                record["name"] = name.text.strip()
            elif company is not None and company.text.strip():
                record["organization"] = company.text.strip()
            if street is not None and street.text.strip():
                record["street"] = street.text.strip()
            if city is not None and city.text.strip():
                record["city"] = city.text.strip()
            if state is not None and state.text.strip():
                record["state"] = state.text.strip()

            # Handling ZIP or ZIP+4 formats
            if zip_code is not None and zip_code.text.strip():
                zip_text = zip_code.text.strip()
                zip_pattern = re.match(r"(\d{5})(?:\s*-\s*(\d{4}))?", zip_text)
                if zip_pattern:
                    zip_formatted = zip_pattern.group(1)
                    if zip_pattern.group(2):
                        zip_formatted += f"-{zip_pattern.group(2)}"
                    record["zip"] = zip_formatted

            if "name" in record or "organization" in record:
                addresses.append(record)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return []

    return addresses


# Returns list of dictionaries filled with properties
def parse_tsv(file_path):
    addresses = []
    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                record = {}

                # Check if 'last' contains an organization name
                last_name = row.get("last", "").strip()
                if any(
                    keyword in last_name.lower()
                    for keyword in ["llc", "company", "inc"]
                ):
                    record["organization"] = last_name
                elif (
                    row.get("organization", "").strip()
                    and row.get("organization").strip() != "N/A"
                ):
                    record["organization"] = row.get("organization").strip()
                else:
                    # Ignore "N/M/N"
                    name_parts = [
                        row.get(part).strip()
                        for part in ["first", "middle", "last"]
                        if row.get(part, "").strip()
                        and row.get(part).strip().upper() != "N/M/N"
                    ]
                    if name_parts:
                        record["name"] = " ".join(name_parts)

                # Continue with the rest of the address processing
                if row.get("address", "").strip():
                    record["street"] = row.get("address").strip()
                if row.get("city", "").strip():
                    record["city"] = row.get("city").strip()
                if row.get("county", "").strip():
                    record["county"] = row.get("county").strip()
                if row.get("state", "").strip():
                    record["state"] = row.get("state").strip()
                zip_code = row.get("zip", "").strip()
                if zip_code:
                    # Handling ZIP or ZIP+4
                    zip4 = row.get("zip4", "").strip()
                    if zip4 and zip4 != "N/A":
                        zip_code += f"-{zip4}"
                    record["zip"] = zip_code

                addresses.append(record)
    except csv.Error as e:
        print(f"Error parsing TSV: {e}", file=sys.stderr)
        sys.exit(1)
    return addresses


# Returns list of dictionaries filled with properties
def parse_txt(file_path):
    addresses = []
    with open(file_path, "r") as file:
        # Holds the current entry
        record = {}
        for line in file:
            line = line.strip()
            if not line:
                if record:
                    addresses.append(record)
                    record = {}
            elif "name" not in record:
                record["name"] = line
            elif "street" not in record:
                record["street"] = line
            elif "city" not in record:
                # Checking if "COUNTY" row exists
                if "COUNTY" in line:
                    record["county"] = line.replace(" COUNTY", "")
                else:
                    parts = line.rsplit(",", 1)
                    record["city"] = parts[0].strip()
                    state_zip_parts = parts[1].rsplit(" ", 1)
                    record["state"] = state_zip_parts[0].strip()
                    record["zip"] = state_zip_parts[1].strip().rstrip("-")
        if record:
            addresses.append(record)
    return addresses


def main():
    parser = argparse.ArgumentParser(
        description="Parse and combine address files into a JSON file"
    )
    parser.add_argument(
        "file_paths", metavar="FILE", nargs="+", help="file paths of input files"
    )
    args = parser.parse_args()
    all_addresses = []
    for file_path in args.file_paths:
        _, extension = os.path.splitext(file_path)
        try:
            if extension == ".xml":
                addresses = parse_xml(file_path)
            elif extension == ".tsv":
                addresses = parse_tsv(file_path)
            elif extension == ".txt":
                addresses = parse_txt(file_path)
            else:
                print(f"Error: Unsupported file type: {extension}", file=sys.stderr)
                sys.exit(1)
            all_addresses.extend(addresses)
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    # Sorting by zip
    sorted_addresses = sorted(all_addresses, key=lambda r: r.get("zip", ""))
    json_output = json.dumps(sorted_addresses, indent=2)
    print(json_output)


if __name__ == "__main__":
    main()
