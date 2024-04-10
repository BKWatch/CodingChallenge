import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
import csv
import re


def parse_xml(xml_file):
    """Parses an XML file containing address information and returns a list of address dictionaries."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    addresses = []

    # Parse each entity in the XML file
    for entity in root.findall("./ENTITY/ENT"):
        name = entity.find("NAME").text.strip()
        organization = entity.find("COMPANY").text.strip()
        street = entity.find("STREET").text.strip()
        city = entity.find("CITY").text.strip()
        state = entity.find("STATE").text.strip()
        zip_code = entity.find("POSTAL_CODE").text.strip().replace(" ", "")

        if zip_code.endswith("-"):
            zip_code = zip_code[:-1]

        address = {
            "name": name if name else None,
            "organization": organization if organization else None,
            "street": street if street else None,
            "city": city if city else None,
            "county": None,
            "state": state if state else None,
            "zip": zip_code if zip_code else None,
        }

        keys_to_remove = []
        for k in address.keys():
            if address[k] is None:
                keys_to_remove.append(k)

        for k in keys_to_remove:
            del address[k]

        addresses.append(address)

    return addresses


def parse_address(lines):
    """Parses a single address entry from multiple lines and returns a dict representing the address."""
    address = {
        "name": None,
        "organization": None,
        "street": None,
        "city": None,
        "county": None,
        "state": None,
        "zip": None,
    }

    # Regex to match ZIP code
    zip_regex = r"(\d{5}-\d{4}|\d{5}-?)$"

    # Process the lines for a single address block
    line_count = len(lines)
    lines = [line.strip() for line in lines if line.strip()]

    if line_count >= 3:
        address["name"] = lines[0]
        address["street"] = lines[1]

        # Check county existence
        last_line = lines[-1]
        if "COUNTY" in lines[-2].upper():
            address["county"] = lines[-2]
            last_line = lines[-1]

        # Last line is always state, zip and potentially city
        state_city_zip = last_line.split(",")
        address["city"] = state_city_zip[0].strip()
        state_zip = state_city_zip[1].strip()

        # Use regex to separate state and zip
        match = re.search(zip_regex, state_zip)
        if match:
            address["zip"] = match.group()
            address["state"] = state_zip[: match.start()].strip()
        else:
            address["state"] = state_zip

        if address["zip"].endswith("-"):
            address["zip"] = address["zip"][:-1]

        keys_to_remove = []
        for k in address.keys():
            if address[k] is None:
                keys_to_remove.append(k)

        for k in keys_to_remove:
            del address[k]

    return address


def parse_txt(file_path):
    """
    Parses a TXT file containing address information and returns a list of address dictionaries.
    """
    addresses = []

    # Read the file and split it into blocks of addresses
    try:
        with open(file_path, "r") as file:
            contents = file.read()
            blocks = contents.strip().split("\n\n")
            for block in blocks:
                lines = block.split("\n")
                if lines:
                    address = parse_address(lines)
                    if address["zip"]:  # Only add if there is a ZIP code
                        addresses.append(address)
    except Exception as e:
        print(f"Error parsing TXT file '{file_path}': {str(e)}")

    return addresses


def parse_tsv(file_path):
    """
    Parses a TSV file containing address information and returns a list of address dictionaries.
    """
    addresses = []

    # Read the TSV file and parse each row
    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                if row["middle"] == "N/M/N":
                    name = f"{row['first']} {row['last']}".strip()
                else:
                    name = f"{row['first']} {row['middle']} {row['last']}".strip()
                organization = row["organization"].strip()
                street = row["address"].strip()
                city = row["city"].strip()
                state = row["state"].strip()
                county = row["county"].strip()
                zip_code = row["zip"].split(" ")[0].strip()
                zip4_code = row["zip4"].strip()
                if name != "":
                    addresses.append(
                        {
                            "name": name,
                            "street": street,
                            "city": city,
                            "state": state,
                            "county": county if county is not None else None,
                            "zip": (
                                zip_code + "-" + zip4_code if zip4_code else zip_code
                            ),
                        }
                    )
                else:
                    addresses.append(
                        {
                            "organization": organization,
                            "street": street,
                            "city": city,
                            "state": state,
                            "county": county if county is not None else None,
                            "zip": (
                                zip_code + "-" + zip4_code if zip4_code else zip_code
                            ),
                        }
                    )
                if addresses[-1]["county"] == "":
                    del addresses[-1]["county"]
    except Exception as e:
        print(f"Error parsing TSV file {file_path}: {e}", file=sys.stderr)
        return None
    return addresses


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Parse and combine addresses from XML, TSV, and TXT files."
    )

    # Add positional argument for file paths
    parser.add_argument(
        "files",
        metavar="file",
        type=str,
        nargs="+",
        help="Pathnames of files in XML, TSV, or TXT formats",
    )
    args = parser.parse_args()

    addresses = []

    # Process each file
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".xml":
            try:
                addresses.extend(parse_xml(file_path))
            except Exception as e:
                print(f"Error parsing XML file '{file_path}': {e}", file=sys.stderr)
                sys.exit(1)
        elif file_ext == ".tsv":
            try:
                addresses.extend(parse_tsv(file_path))
            except Exception as e:
                print(f"Error parsing TSV file '{file_path}': {e}", file=sys.stderr)
                sys.exit(1)
        elif file_ext == ".txt":
            try:
                addresses.extend(parse_txt(file_path))
            except Exception as e:
                print(f"Error parsing TXT file '{file_path}': {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                f"Error: Unsupported file format for '{file_path}'. Only XML, TSV, and TXT are supported.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Sort the addresses by ZIP code and print the result
    if addresses:
        sorted_addresses = sorted(addresses, key=lambda x: x["zip"])
        print(json.dumps(sorted_addresses, indent=2))
        sys.exit(0)
    else:
        print("No valid addresses found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
