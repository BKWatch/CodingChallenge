import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET


def parse_input_file(file_path):
    """
    Parses an input file based on its extension and returns the parsed data as a list of dictionaries.

    Args:
        file_path (str): The path to the input file.

    Returns:
        list: A list of dictionaries containing the parsed data.
    """
    _, file_extension = os.path.splitext(file_path)
    if file_extension == ".xml":
        return parse_xml(file_path)
    elif file_extension == ".tsv":
        return parse_tsv(file_path)
    elif file_extension == ".txt":
        return parse_txt(file_path)
    else:
        sys.stderr.write(f"Unsupported file format: {file_extension}\n")
        sys.exit(1)


def parse_xml(file_path):
    """
    Parses an XML file and extracts address information.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        list: A list of dictionaries containing the parsed address information.
    """
    addresses = []
    try:
        # Parse XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Extract address information from XML elements by extracting elements of entity
        for ent in root.findall("ENTITY/ENT"):
            address_data = {}
            name = ent.find("NAME").text.strip()
            company = ent.find("COMPANY").text.strip()
            street = ent.find("STREET").text.strip()
            city = ent.find("CITY").text.strip()
            state = ent.find("STATE").text.strip()
            postal_code = (
                ent.find("POSTAL_CODE").text.strip().split(" - ")[0]
            )  # Remove the '-' and extra spaces
            country = (
                ent.find("COUNTRY").text.strip()
                if ent.find("COUNTRY") is not None
                else None
            )

            # Store address data in a dictionary
            if name:
                address_data["name"] = name
            if company:
                address_data["organization"] = company
            address_data["street"] = street
            address_data["city"] = city
            address_data["state"] = state
            address_data["zip"] = postal_code
            if country:
                address_data["country"] = country

            addresses.append(address_data)
    except Exception as e:
        sys.stderr.write(f"Error parsing XML file: {e}\n")
        sys.exit(1)
    return addresses


def parse_tsv(file_path):
    """
    Parses a TSV (Tab-Separated Values) file and extracts address information.

    Args:
        file_path (str): The path to the TSV file.

    Returns:
        list: A list of dictionaries containing the parsed address information.
    """
    addresses = []
    try:
        # Parse TSV file
        with open(file_path, "r", encoding="utf-8") as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter="\t")
            # Iterate over rows in the TSV file and extract address information
            for row in reader:
                address_data = {}
                # combining first 3 cols for name
                name = f"{row['first']} {row['middle']} {row['last']}".strip()
                organization = row["organization"].strip()
                street = row["address"].strip()
                city = row["city"].strip()
                state = row["state"].strip()
                county = row["county"].strip()
                zip_code = row["zip"].strip()
                zip4 = row["zip4"].strip() if "zip4" in row else None

                # Store address data in a dictionary
                if name:
                    address_data["name"] = name

                if organization != "N/A":
                    address_data["organization"] = organization

                address_data["street"] = street
                address_data["city"] = city
                address_data["state"] = state
                address_data["county"] = county
                address_data["zip"] = zip_code
                address_data["zip4"] = zip4
                addresses.append(address_data)
    except Exception as e:
        sys.stderr.write(f"Error parsing TSV file: {e}\n")
        sys.exit(1)
    return addresses


def parse_txt(file_path):
    """
    Parses a TXT file containing address information.

    Args:
        file_path (str): The path to the TXT file.

    Returns:
        list: A list of dictionaries containing the parsed address information.
    """
    addresses = []

    with open(file_path, "r") as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        address_dict = {}
        # Check if there are enough lines left in the file
        if i + 4 <= len(lines):
            # Check if the line is not empty
            if lines[i].strip():
                name = lines[i].strip()
                street = lines[i + 1].strip()

                # Extract city, state, and zip code
                city_state_zip = lines[i + 2].strip().split(", ")[-1].split(" ")
                city = city_state_zip[0]
                state_zip = city_state_zip[1:]
                state = state_zip[0] if len(state_zip) >= 1 else None
                zip_code = state_zip[1] if len(state_zip) == 2 else None
                county = lines[i + 2].strip().split(", ")[0]

                address_dict["name"] = name
                address_dict["street"] = street
                address_dict["city"] = city
                address_dict["county"] = county
                address_dict["state"] = state
                if zip_code:
                    address_dict["zip"] = zip_code

                addresses.append(address_dict)

                # Move to the next block of addresses (skip empty line)
                i += 4
            else:
                # Skip empty line
                i += 1
        else:
            # Break out of the loop if there are no more lines left
            break

    return addresses


def main():
    """
    Main function that parses input files and outputs the parsed data as JSON.
    """
    parser = argparse.ArgumentParser(
        description="Parse US names and addresses files and output as JSON."
    )
    parser.add_argument("files", nargs="+", help="List of file paths to parse.")
    args = parser.parse_args()

    if not args.files:
        sys.stderr.write("No input files provided.\n")
        sys.exit(1)

    combined_addresses = []
    for file_path in args.files:
        if not os.path.isfile(file_path):
            sys.stderr.write(f"File not found: {file_path}\n")
            sys.exit(1)
        combined_addresses.extend(parse_input_file(file_path))

    if not combined_addresses:
        sys.stderr.write("No addresses found in input files.\n")
        sys.exit(1)

    combined_addresses.sort(key=lambda x: x.get("zip", ""))

    print(json.dumps(combined_addresses, indent=2))


if __name__ == "__main__":
    main()
