import json
import csv
import xml.etree.ElementTree as ET
import sys
import argparse
import re
import os


# Returns filled list with properties from an XML file
def parse_xml(file_path):
    addresses = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for ent in root.findall("./ENTITY/ENT"):
            record = {}
            name = ent.find("NAME")
            company = ent.find("COMPANY")
            if name is not None and name.text.strip():
                record["name"] = name.text.strip()
            elif company is not None and company.text.strip():
                record["organization"] = company.text.strip()
            street = ent.find("STREET")
            if street is not None and street.text.strip():
                record["street"] = street.text.strip()
            city = ent.find("CITY")
            if city is not None and city.text.strip():
                record["city"] = city.text.strip()
            state = ent.find("STATE")
            if state is not None and state.text.strip():
                record["state"] = state.text.strip()
            zip_code = ent.find("POSTAL_CODE")
            if zip_code is not None and zip_code.text.strip():
                zip_text = zip_code.text.strip()
                # Check format for ZIP or ZIP+4
                zip_pattern = re.match(r"(\d{5})(?:\s*-\s*(\d{4}))?", zip_text)
                if zip_pattern:
                    zip_formatted = zip_pattern.group(1)
                    if zip_pattern.group(2):
                        zip_formatted += f"-{zip_pattern.group(2)}"
                    record["zip"] = zip_formatted
            if "name" in record or "organization" in record:
                addresses.append(record)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)
    return addresses


# Returns filled list with properties from a TSV file
def parse_tsv(file_path):
    addresses = []
    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                record = {}
                if (row.get("organization", "").strip()
                    and row.get("organization").strip() != "N/A"
                ):
                    record["organization"] = row.get("organization").strip()
                else:
                    name_parts = [
                        row.get(part).strip()
                        for part in ["first", "middle", "last"]
                        if row.get(part, "").strip()
                    ]
                    if name_parts:
                        record["name"] = " ".join(name_parts)
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
                    # Checking if ZIP or ZIP+4
                    zip4 = row.get("zip4", "").strip()
                    if zip4 and zip4 != "N/A":
                        zip_code += f"-{zip4}"
                    record["zip"] = zip_code

                addresses.append(record)
    except csv.Error as e:
        print(f"Error when parsing the TSV file: {e}", file=sys.stderr)
        sys.exit(1)
    return addresses


# Returns filled list with properties from a text file
def parse_txt(file_path):
    addresses = []
    with open(file_path, "r") as file:
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
        description="Extract address from input files into a JSON file"
    )
    parser.add_argument(
        "-p", "--paths", 
        nargs="+", 
        help="file paths of input files. For example: python3 challenge.py -p input/input1.xml input/input2.tsv input/input3.txt", 
        required=True
    )
    args = parser.parse_args()

    addresses_list = []
    for file_path in args.paths:
        print(f"Processing file: {file_path}")
        _, extension = os.path.splitext(file_path)
        try:
            if extension == ".xml":
                addresses = parse_xml(file_path)
            elif extension == ".tsv":
                addresses = parse_tsv(file_path)
            elif extension == ".txt":
                addresses = parse_txt(file_path)
            else:
                print(f"Error because unsupported file type: {extension}", file=sys.stderr)
                sys.exit(1)
            addresses_list.extend(addresses)
        except FileNotFoundError:
            print(f"Error because file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error when parsing file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    print("Finished processing files")
    # Sort the addresses by zip in ascending order 
    sorted_addresses = sorted(addresses_list, key=lambda x: x.get("zip", ""))
    json_output = json.dumps(sorted_addresses, indent=2)
    print("Writing to output file ...")
    # Write to output file
    if not os.path.exists("output"):
        os.makedirs("output")
    with open("output/extracted_addresses.json", "w") as json_file:
        json_file.write(json_output)
        print("Finished writing to output file output/extracted_addresses.json")
        print("Done")


if __name__ == "__main__":
    main()